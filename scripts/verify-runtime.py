#!/usr/bin/env python3
"""Run the Linux bridge against disposable MQTT, LAN and HTTPS proxy fixtures."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
from queue import Queue
import socket
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


def exchange(conn, requests):
    conn.settimeout(TIMEOUT)
    with conn.makefile("rb") as stream:
        check(receive(stream)[0] == 1, "broker fixture did not see MQTT CONNECT")
        conn.sendall(b"\x20\x02\x00\x00")
        deadline = time.monotonic() + TIMEOUT
        while time.monotonic() < deadline:
            kind, packet = receive(stream)
            if kind == 8:
                conn.sendall(b"\x90\x03" + packet[:2] + b"\x00")
            elif kind == 12:
                conn.sendall(b"\xd0\x00")
            elif kind == 3:
                size = int.from_bytes(packet[:2], "big")
                if packet[2:2+size].decode() == CONFIG_TOPIC:
                    config = json.loads(packet[2+size:])
                    break
        else:
            raise AssertionError("light discovery config never arrived")
        check(not config["effect"], "unexpected online scenes in fixture")
        for message, command in [
            ({"state": "OFF"}, {"cmd": "turn", "data": {"value": 0}}),
            ({"state": "ON", "brightness": 42}, {"cmd": "brightness", "data": {"value": 42}}),
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
                    if state.get("brightness") == 42 and state.get("color_temp") == 250:
                        break
        else:
            raise AssertionError("bridge did not publish the LAN fixture's updated status")
        return tuple(config["device"]["identifiers"]), config["unique_id"], config["command_topic"]


def bridge(binary, proxy_mode=None, http=False, blank_key=False):
    with fixtures(proxy_mode) as (requests, cloud, proxy), tempfile.TemporaryDirectory() as tmp, \
            socket.create_server((IP, 0)) as broker, tempfile.TemporaryFile() as logs:
        env = {"GOVEE_CACHE_DIR": tmp, "HTTPS_PROXY": proxy, "NO_PROXY": IP,
               "GOVEE_MQTT_HOST": IP, "GOVEE_MQTT_PORT": str(broker.getsockname()[1])}
        cache = Path(tmp) / "govee2mqtt-cache.sqlite"
        if proxy_mode:
            env["GOVEE_API_KEY"] = SECRET
            cache.write_text("synthetic invalid database")
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
                    else:
                        check(cloud.empty(), "cloud request without opt-in")
                    if http:
                        assert_http(process.pid, http_port)
                    else:
                        check(not listeners(process.pid), "unexpected default TCP listener")
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
                if proxy_mode:
                    check("Platform API refresh failed;" in output, "cloud failure was not handled")
                    check(cache.read_text() == "synthetic invalid database",
                          "bridge overwrote the invalid DB without permission")
            return identity


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
    expected = bridge(binary)
    for restart in range(3):
        check(bridge(binary, blank_key=restart == 2) == expected, "MQTT identity changed after restart")
    for failure in ["503", "disconnect"]:
        check(bridge(binary, proxy_mode=failure) == expected, "MQTT identity changed on cloud failure")
    check(bridge(binary, http=True) == expected, "MQTT identity changed on HTTP opt-in")
    print("PASS: LAN commands/readback, three MQTT restarts, HTTP opt-in, "
          "cloud 503 and disconnect, corrupt cache preserved")


if __name__ == "__main__":
    main()
