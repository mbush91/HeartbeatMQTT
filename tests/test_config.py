import pytest

from heartbeatmqtt.config import load_settings


def test_load_settings_defaults(monkeypatch):
    monkeypatch.setenv("MQTT_URL", "mqtt://broker.local")
    monkeypatch.setenv("MQTT_TOPIC", "devices/heartbeat")
    monkeypatch.delenv("MQTT_USERNAME", raising=False)
    monkeypatch.delenv("MQTT_PASSWORD", raising=False)
    monkeypatch.delenv("MQTT_PASS", raising=False)

    settings = load_settings()

    assert settings.mqtt_host == "broker.local"
    assert settings.mqtt_port == 1883
    assert settings.mqtt_tls is False
    assert settings.mqtt_message == "heartbeat"
    assert settings.heartbeat_interval_seconds == 300.0
    assert settings.publish_immediately is True


def test_tls_and_custom_values(monkeypatch):
    monkeypatch.setenv("MQTT_URL", "mqtts://broker.example.com")
    monkeypatch.setenv("MQTT_TOPIC", "devices/heartbeat")
    monkeypatch.setenv("MQTT_USERNAME", "user")
    monkeypatch.setenv("MQTT_PASS", "secret")
    monkeypatch.setenv("MQTT_MESSAGE", "alive")
    monkeypatch.setenv("MQTT_QOS", "2")
    monkeypatch.setenv("MQTT_RETAIN", "true")
    monkeypatch.setenv("HEARTBEAT_INTERVAL_MINUTES", "2.5")
    monkeypatch.setenv("HEARTBEAT_PUBLISH_IMMEDIATELY", "false")

    settings = load_settings()

    assert settings.mqtt_port == 8883
    assert settings.mqtt_tls is True
    assert settings.mqtt_password == "secret"
    assert settings.mqtt_message == "alive"
    assert settings.mqtt_qos == 2
    assert settings.mqtt_retain is True
    assert settings.heartbeat_interval_seconds == 150.0
    assert settings.publish_immediately is False


def test_rejects_invalid_qos(monkeypatch):
    monkeypatch.setenv("MQTT_URL", "mqtt://broker.local")
    monkeypatch.setenv("MQTT_TOPIC", "devices/heartbeat")
    monkeypatch.setenv("MQTT_QOS", "3")

    with pytest.raises(RuntimeError, match="MQTT_QOS"):
        load_settings()
