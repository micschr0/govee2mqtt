#!/usr/bin/env python3
"""Run the Linux bridge against disposable MQTT, LAN and HTTPS proxy fixtures."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
from queue import Queue
import socket
import ssl
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

IP = "127.0.0.1"
ID = "00:00:00:00:00:00:00:01"
CONFIG_TOPIC = "homeassistant/light/gv2mqtt-0000000000000001/config"
SECRET = "synthetic-cloud-key"
TIMEOUT = 45
ASSETS = Path(__file__).resolve().parents[1] / "govee2mqtt_security_local/local-source/assets"


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def receive(stream):
    header = stream.read(1)
    check(header, "bridge closed MQTT")
    size = 0
    for shift in range(0, 28, 7):
        byte = stream.read(1)[0]
        size |= (byte & 127) << shift
        if byte < 128:
            return header[0] >> 4, stream.read(size)
    raise AssertionError("invalid MQTT packet length")


def publish(conn, topic, message):
    topic = topic.encode()
    payload = struct.pack(">H", len(topic)) + topic + json.dumps(message).encode()
    check(len(payload) < 128, "fixture MQTT packet too large")
    conn.sendall(bytes([0x30, len(payload)]) + payload)


def udp(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((IP, port))
    sock.settimeout(0.25)
    return sock


@contextmanager
def fixtures(proxy_mode):
    with udp(4001) as scans, udp(4003) as commands, socket.create_server((IP, 0)) as proxy:
        stop = threading.Event()
        requests, cloud = Queue(), Queue()

        def lamp():
            scan_data = {"device": ID, "sku": "H6072", "ip": IP}
            for key in ("bleVersionHard", "bleVersionSoft", "wifiVersionHard", "wifiVersionSoft"):
                scan_data[key] = "1"
            state = {"onOff": 1, "brightness": 27, "color": {"r": 0, "g": 0, "b": 0},
                     "colorTemInKelvin": 3000}
            while not stop.is_set():
                for sock in (scans, commands):
                    try:
                        packet, sender = sock.recvfrom(4096)
                    except TimeoutError:
                        continue
                    msg = json.loads(packet)["msg"]
                    kind = msg["cmd"]
                    if kind == "scan" or kind == "devStatus":
                        data = scan_data if kind == "scan" else state
                        sock.sendto(json.dumps({"msg": {"cmd": kind, "data": data}}).encode(),
                                    (sender[0], 4002))
                    else:
                        requests.put(msg)
                        if kind == "brightness":
                            state["brightness"] = msg["data"]["value"]
                            state["onOff"] = 1
                        elif kind == "turn":
                            state["onOff"] = msg["data"]["value"]
                        elif kind == "colorwc":
                            state.update(msg["data"])

        def unavailable_cloud():
            proxy.settimeout(0.25)
            while not stop.is_set():
                try:
                    conn, _ = proxy.accept()
                except TimeoutError:
                    continue
                with conn:
                    conn.settimeout(3)
                    cloud.put(conn.recv(4096))
                    if proxy_mode != "disconnect":
                        conn.sendall(b"HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\n\r\n")

        workers = [threading.Thread(target=fn, daemon=True) for fn in (lamp, unavailable_cloud)]
        for worker in workers:
            worker.start()
        try:
            yield requests, cloud, f"http://{IP}:{proxy.getsockname()[1]}"
        finally:
            stop.set()
            for worker in workers:
                worker.join(4)


def listeners(pid):
    owned = set()
    for fd in Path(f"/proc/{pid}/fd").iterdir():
        try:
            owned.add(os.readlink(fd))
        except FileNotFoundError:
            pass  # The bridge can close a socket while we inspect the table.
    return {
        (path, entry[1]) for path in ("/proc/net/tcp", "/proc/net/tcp6")
        for line in Path(path).read_text().splitlines()[1:]
        if (entry := line.split())[3] == "0A" and f"socket:[{entry[9]}]" in owned
    }


def assert_http(pid, port):
    client = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + 5
    while True:
        try:
            with client.open(f"http://{IP}:{port}/", timeout=1) as response:
                check(response.status == 200, "HTTP opt-in did not serve the WebUI")
            break
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.05)
    check(listeners(pid) == {("/proc/net/tcp", f"0100007F:{port:04X}")},
          "bridge did not bind HTTP exclusively to the selected loopback address")


def exchange(conn, requests, *, brightness=42):
    conn.settimeout(TIMEOUT)
    with conn.makefile("rb") as stream:
        check(receive(stream)[0] == 1, "broker fixture did not see MQTT CONNECT")
        conn.sendall(b"\x20\x02\x00\x00")  # No existing MQTT session.
        missing = {b"homeassistant/status", b"gv2mqtt/light/+/command"}
        config = None
        deadline = time.monotonic() + TIMEOUT
        while time.monotonic() < deadline:
            try:
                kind, packet = receive(stream)
            except TimeoutError:
                break
            if kind == 8:
                offset, grants = 2, bytearray()
                while offset < len(packet):
                    size = int.from_bytes(packet[offset:offset+2], "big")
                    missing.discard(packet[offset+2:offset+2+size])
                    grants.append(0)
                    offset += size + 3
                conn.sendall(bytes([0x90, 2 + len(grants)]) + packet[:2] + grants)
            elif kind == 12:
                conn.sendall(b"\xd0\x00")
            elif kind == 3:
                size = int.from_bytes(packet[:2], "big")
                if packet[2:2+size].decode() == CONFIG_TOPIC:
                    config = json.loads(packet[2+size:])
            if config is not None and not missing:
                break
        check(not missing, f"MQTT connection missing SUBSCRIBE for {sorted(missing)!r}")
        check(config is not None, "light discovery config never arrived")
        check(not config["effect"], "unexpected online scenes in fixture")
        for message, command in [
            ({"state": "OFF"}, {"cmd": "turn", "data": {"value": 0}}),
            ({"state": "ON", "brightness": brightness},
             {"cmd": "brightness", "data": {"value": brightness}}),
            ({"state": "ON", "color_temp": 250}, {
                "cmd": "colorwc", "data": {"color": {"r": 0, "g": 0, "b": 0},
                                           "colorTemInKelvin": 4000},
            }),
        ]:
            publish(conn, config["command_topic"], message)
            check(requests.get(timeout=5) == command, f"incorrect LAN encoding for {message!r}")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            kind, packet = receive(stream)
            if kind == 3:
                size = int.from_bytes(packet[:2], "big")
                if packet[2:2+size].decode() == config["state_topic"]:
                    state = json.loads(packet[2+size:])
                    if state.get("brightness") == brightness and state.get("color_temp") == 250:
                        break
        else:
            raise AssertionError("bridge did not publish the LAN fixture's updated status")
        return (tuple(config["device"]["identifiers"]), config["unique_id"],
                config["command_topic"], config["state_topic"])


def bridge(binary, proxy_mode=None, http=False, blank_key=False, reconnect=False):
    with fixtures(proxy_mode) as (requests, cloud, proxy), tempfile.TemporaryDirectory() as tmp, \
            socket.create_server((IP, 0)) as broker, tempfile.TemporaryFile() as logs:
        env = {"GOVEE_CACHE_DIR": tmp, "HTTPS_PROXY": proxy, "NO_PROXY": IP,
               "GOVEE_MQTT_HOST": IP, "GOVEE_MQTT_PORT": str(broker.getsockname()[1])}
        legacy_cache = Path(tmp) / "govee2mqtt-cache.sqlite"
        legacy_cache.touch(mode=0o600)  # SQLite accepts an empty database file.
        cache = legacy_cache.with_name("govee2mqtt-cache-v2.sqlite")
        if proxy_mode:
            env["GOVEE_API_KEY"] = SECRET
            cache.write_text("synthetic invalid database")
            cache.chmod(0o600)
        elif blank_key:
            env["GOVEE_API_KEY"] = " "
        args = [binary, "serve", "--no-multicast", "--scan", IP]
        if http:
            with socket.create_server((IP, 0)) as reservation:
                http_port = reservation.getsockname()[1]
            args += ["--http-bind", f"{IP}:{http_port}"]
            (Path(tmp) / "assets").symlink_to(ASSETS)
        broker.settimeout(TIMEOUT)
        with subprocess.Popen(args, cwd=tmp, env=env,
                              stdout=logs, stderr=subprocess.STDOUT) as process:
            try:
                conn, _ = broker.accept()
                with conn:
                    identity = exchange(conn, requests)
                    if proxy_mode:
                        check(b"CONNECT openapi.api.govee.com:443" in cloud.get(timeout=5),
                              "cloud fixture did not receive the expected opt-in request")
                    if http:
                        assert_http(process.pid, http_port)
                    else:
                        check(not listeners(process.pid), "unexpected default TCP listener")
                    if reconnect:
                        conn.shutdown(socket.SHUT_RDWR)
                if reconnect:
                    try:
                        conn, _ = broker.accept()
                    except TimeoutError as err:
                        raise AssertionError("bridge did not reconnect after MQTT TCP shutdown") from err
                    with conn:
                        # A different brightness rules out pre-disconnect state as readback.
                        check(exchange(conn, requests, brightness=63) == identity,
                              "MQTT identity changed after TCP reconnect")
                        check(process.poll() is None, "bridge exited during MQTT reconnect")
                if not proxy_mode:
                    check(cloud.empty(), "cloud request without opt-in")
            finally:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
                logs.seek(0)
                output = logs.read().decode(errors="replace")
                if sys.exc_info()[0] is not None:
                    print(output.replace(SECRET, "[redacted]"), file=sys.stderr)
                check(SECRET not in output, "cloud key appeared in bridge logs")
                check(legacy_cache.read_bytes() == b"", "bridge modified the legacy cache")
                if proxy_mode:
                    check("Platform API refresh failed;" in output, "cloud failure was not handled")
                    check("Cloud cache unavailable; continuing without a disk cache" in output,
                          "bridge did not fall back when opening the invalid v2 cache")
                    check(cache.read_text() == "synthetic invalid database",
                          "bridge overwrote the invalid v2 cache")
                else:
                    check(not any(cache.parent.glob(f"{cache.name}*")),
                          "bridge created a cache without cloud opt-in")
            return identity


def verify_mqtt_tls(binary):
    with tempfile.TemporaryDirectory() as cwd:
        root = Path(cwd)

        def openssl(*args):
            subprocess.run(["openssl", *args], cwd=cwd, capture_output=True, check=True, timeout=10)

        for name in ("ca", "other-ca"):
            openssl("req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:P-256",
                    "-nodes", "-subj", f"/CN=MQTT fixture {name}", "-days", "1",
                    "-addext", "basicConstraints=critical,CA:TRUE",
                    "-addext", "keyUsage=critical,keyCertSign,cRLSign",
                    "-keyout", f"{name}.key", "-out", f"{name}.pem")
        openssl("req", "-new", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:P-256",
                "-nodes", "-subj", "/CN=mqtt.fixture.invalid",
                "-keyout", "server.key", "-out", "server.csr")
        (root / "server.ext").write_text("subjectAltName=DNS:localhost\nextendedKeyUsage=serverAuth\n")
        openssl("x509", "-req", "-in", "server.csr", "-CA", "ca.pem", "-CAkey", "ca.key",
                "-CAcreateserial", "-days", "1", "-extfile", "server.ext", "-out", "server.pem")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(root / "server.pem", root / "server.key")
        args = [binary, "serve", "--no-multicast"]
        env = {"GOVEE_CACHE_DIR": cwd, "GOVEE_MQTT_HOST": "localhost"}

        (root / "malformed.pem").write_text("not a PEM certificate")
        with socket.create_server((IP, 0)) as broker:
            invalid_port = str(broker.getsockname()[1])
            for ca, error in (("missing.pem", b"MQTT TLS CA file"),
                              ("", b"MQTT TLS CA file"),
                              (".", b"MQTT TLS CA file"),
                              ("malformed.pem", b"MQTT TLS connection failed")):
                result = subprocess.run(args, cwd=cwd,
                                        env={**env, "GOVEE_MQTT_TLS_CA": ca,
                                             "GOVEE_MQTT_PORT": invalid_port},
                                        capture_output=True, timeout=5)
                check(result.returncode == 1 and error in result.stderr,
                      f"invalid TLS CA {ca!r} did not fail startup: {result.stderr!r}")
        result = subprocess.run(args, cwd=cwd, env={**env, "GOVEE_MQTT_TLS_CA": "ca.pem",
                                                   "GOVEE_MQTT_PORT": "0"},
                                capture_output=True, timeout=5)
        check(result.returncode == 1 and b"MQTT TLS requires a nonzero TCP port" in result.stderr,
              "MQTT TLS permitted port 0")

        for label, host, ca, cli in [
            ("trusted CA", "localhost", "missing.pem", ["--mqtt-tls-ca", "ca.pem"]),
            ("wrong CA", "localhost", "other-ca.pem", []),
            ("hostname mismatch", IP, "ca.pem", []),
            ("plaintext listener", "localhost", "ca.pem", []),
        ]:
            with socket.create_server((IP, 0)) as broker:
                broker.settimeout(5)
                config = {**env, "GOVEE_MQTT_TLS_CA": ca, "GOVEE_MQTT_HOST": host,
                          "GOVEE_MQTT_PORT": str(broker.getsockname()[1])}
                with subprocess.Popen(args + cli, cwd=cwd, env=config, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT) as process:
                    try:
                        conn, _ = broker.accept()
                        with conn:
                            conn.settimeout(5)
                            check(conn.recv(1, socket.MSG_PEEK) == b"\x16",
                                  f"{label}: connection did not start with TLS")
                            if cli:
                                with context.wrap_socket(conn, server_side=True) as secure, \
                                        secure.makefile("rb") as stream:
                                    check(receive(stream)[0] == 1, "TCP/TLS did not carry MQTT CONNECT")
                                    secure.sendall(b"\x20\x02\x00\x00")
                                    secure.settimeout(10)  # MQTT starts after a 5-second LAN grace period.
                                    check(receive(stream)[0] == 8, "TLS did not carry MQTT SUBSCRIBE")
                            elif label != "plaintext listener":
                                try:
                                    with context.wrap_socket(conn, server_side=True):
                                        raise AssertionError(f"{label}: TLS handshake succeeded")
                                except ssl.SSLError:
                                    pass
                        if not cli:
                            output, _ = process.communicate(timeout=15)
                            check(process.returncode == 1 and b"MQTT TLS" in output,
                                  f"{label}: did not fail MQTT TLS startup\n{output.decode()}")
                            broker.setblocking(False)
                            while True:
                                try:
                                    retry, _ = broker.accept()
                                except BlockingIOError:
                                    break
                                with retry:
                                    retry.settimeout(1)
                                    check(retry.recv(1) in (b"", b"\x16"),
                                          f"{label}: plaintext MQTT retry")
                    finally:
                        if process.poll() is None:
                            process.kill()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    with tempfile.TemporaryDirectory() as cwd:
        invalid = subprocess.run([binary, "serve", "--http-bind", "not-an-address"],
                                 cwd=cwd, env={}, capture_output=True, timeout=5)
    check(invalid.returncode != 0 and b"not-an-address" in invalid.stderr,
          "invalid HTTP bind did not fail at startup")
    verify_mqtt_tls(binary)
    expected = bridge(binary, reconnect=True)
    for restart in range(3):
        check(bridge(binary, blank_key=restart == 2) == expected, "MQTT identity changed after restart")
    for failure in ["503", "disconnect"]:
        check(bridge(binary, proxy_mode=failure) == expected, "MQTT identity changed on cloud failure")
    check(bridge(binary, http=True) == expected, "MQTT identity changed on HTTP opt-in")
    print("PASS: LAN commands/readback, MQTT TCP reconnect with fresh subscriptions and stable identity, "
          "three bridge restarts, HTTP opt-in, "
          "cloud 503 and disconnect, corrupt cache preserved, MQTT TLS without fallback")


if __name__ == "__main__":
    main()
