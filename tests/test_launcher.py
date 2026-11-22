import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

LAUNCHER = Path(__file__).resolve().parents[1] / "govee2mqtt_security_local/run.sh"
STUB = """
bashio::config.has_value() { [[ -n "${!1}" ]]; }
bashio::config() {
    [[ "$1" != "${fail_option:-}" ]] || return 1
    printf '%s' "${!1}"
}
bashio::services.available() { [[ "$broker" = available ]]; }
bashio::services() {
    [[ "$2" != "${fail_service:-}" ]] || return 1
    case "$2" in
        host) printf 'broker.fixture';;
        port) printf '2883';;
        username) printf 'fixture-account';;
        password) printf 'supervisor-secret';;
    esac
}
bashio::log.info() { printf '%s\\n' "$*"; }
bashio::log.error() { printf '%s\\n' "$*" >&2; }
bashio::exit.nok() { printf '%s\\n' "$*" >&2; exit 1; }
sleep() { :; }
timeout() {
    [[ "$broker" = available && "$6" = broker.fixture && "$7" = 2883 ]]
}
cd() { [[ "$1" = /app ]]; }
exec() {
    [[ "$*" = "/app/govee serve" ]] || exit 2
    python3 -c 'import json, os, sys; json.dump(dict(os.environ), sys.stdout)' > "$observed"
}
"""


class LauncherTest(unittest.TestCase):
    def launch(self, **options):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            stub = root / "bashio.sh"
            stub.write_text(STUB)
            observed = root / "observed.json"
            result = subprocess.run(
                ["bash", LAUNCHER],
                env={"PATH": os.environ["PATH"], "BASH_ENV": str(stub),
                     "observed": str(observed), **options},
                capture_output=True, text=True, timeout=10,
            )
            return result, json.loads(observed.read_text()) if observed.exists() else {}

    def test_explicit_options_keep_credentials_out_of_logs(self):
        result, env = self.launch(
            mqtt_host="mqtt.fixture", mqtt_port="1889", mqtt_username="explicit-user",
            mqtt_password="mqtt-secret", govee_email="private-email",
            govee_password="line-one\nline-two", govee_api_key="private-key",
            http_bind="127.0.0.1:8056", no_multicast="true", temperature_scale="F",
            debug_level="govee=trace", broadcast_all="false", global_broadcast="true",
            scan="192.0.2.10",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({key: value for key, value in env.items()
                          if key.startswith("GOVEE_")}, {
            "GOVEE_MQTT_HOST": "mqtt.fixture", "GOVEE_MQTT_PORT": "1889",
            "GOVEE_MQTT_USER": "explicit-user", "GOVEE_MQTT_PASSWORD": "mqtt-secret",
            "GOVEE_EMAIL": "private-email", "GOVEE_PASSWORD": "line-one\nline-two",
            "GOVEE_API_KEY": "private-key", "GOVEE_HTTP_BIND": "127.0.0.1:8056",
            "GOVEE_LAN_NO_MULTICAST": "true", "GOVEE_TEMPERATURE_SCALE": "F",
            "GOVEE_LAN_BROADCAST_ALL": "false", "GOVEE_LAN_BROADCAST_GLOBAL": "true",
            "GOVEE_LAN_SCAN": "192.0.2.10",
        })
        self.assertEqual(env["RUST_LOG"], "govee=trace")
        for value in ["mqtt-secret", "private-email", "line-one", "line-two", "private-key"]:
            self.assertNotIn(value, result.stdout + result.stderr)

    def test_supervisor_settings_allow_explicit_overrides_and_no_cloud(self):
        result, env = self.launch(broker="available", mqtt_port="2884")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(env["GOVEE_MQTT_HOST"], "broker.fixture")
        self.assertEqual(env["GOVEE_MQTT_PORT"], "2884")
        self.assertEqual(env["GOVEE_MQTT_PASSWORD"], "supervisor-secret")
        self.assertNotIn("supervisor-secret", result.stdout + result.stderr)
        self.assertNotIn("GOVEE_HTTP_BIND", env)
        self.assertNotIn("GOVEE_API_KEY", env)
        self.assertNotIn("GOVEE_MQTT_TLS_CA", env)

    def test_explicit_broker_can_opt_into_tls(self):
        result, env = self.launch(mqtt_host="broker.fixture", mqtt_tls_ca="/app/config/local CA.pem")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(env["GOVEE_MQTT_HOST"], "broker.fixture")
        self.assertEqual(env["GOVEE_MQTT_TLS_CA"], "/app/config/local CA.pem")
        self.assertNotIn("GOVEE_MQTT_PORT", env)
        self.assertNotIn("GOVEE_MQTT_PASSWORD", env)

    def test_tls_without_explicit_host_does_not_use_supervisor_broker(self):
        result, env = self.launch(broker="available", mqtt_tls_ca="/app/config/ca.pem")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(env, {})
        self.assertIn("mqtt_tls_ca requires mqtt_host", result.stderr)
        self.assertNotIn("waiting for the Mosquitto broker", result.stdout)

    def test_missing_broker_fails_before_starting_bridge(self):
        result, env = self.launch()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(env, {})
        self.assertIn("Mosquitto MQTT broker is not available", result.stderr)

    def test_failed_option_read_stops_without_leaking_credentials(self):
        result, env = self.launch(
            mqtt_host="mqtt.fixture", mqtt_password="mqtt-secret",
            govee_password="cloud-secret", fail_option="govee_password",
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(env, {})
        self.assertIn("Cannot read add-on option govee_password", result.stderr)
        self.assertNotIn("mqtt-secret", result.stdout + result.stderr)
        self.assertNotIn("cloud-secret", result.stdout + result.stderr)

    def test_failed_supervisor_credentials_stop_before_starting_bridge(self):
        result, env = self.launch(broker="available", fail_service="password")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(env, {})
        self.assertIn("Cannot read the MQTT service configuration", result.stderr)
        self.assertNotIn("supervisor-secret", result.stdout + result.stderr)
