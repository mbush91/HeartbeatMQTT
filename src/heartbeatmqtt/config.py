from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class Settings:
    mqtt_url: str
    mqtt_host: str
    mqtt_port: int
    mqtt_tls: bool
    mqtt_username: str | None
    mqtt_password: str | None
    mqtt_topic: str
    mqtt_message: str
    mqtt_qos: int
    mqtt_retain: bool
    mqtt_keepalive_seconds: int
    mqtt_connect_timeout_seconds: float
    mqtt_publish_timeout_seconds: float
    mqtt_retry_seconds: float
    heartbeat_interval_seconds: float
    publish_immediately: bool


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _float(name: str, default: float, *, minimum: float | None = None) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        value = default
    else:
        try:
            value = float(raw)
        except ValueError as exc:
            raise RuntimeError(f"{name} must be a number") from exc
    if minimum is not None and value < minimum:
        raise RuntimeError(f"{name} must be >= {minimum}")
    return value


def _int(name: str, default: int, *, minimum: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        value = default
    else:
        try:
            value = int(raw)
        except ValueError as exc:
            raise RuntimeError(f"{name} must be an integer") from exc
    if minimum is not None and value < minimum:
        raise RuntimeError(f"{name} must be >= {minimum}")
    return value


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be true/false, yes/no, on/off, or 1/0")


def load_settings() -> Settings:
    mqtt_url = _required("MQTT_URL")
    mqtt_topic = _required("MQTT_TOPIC")
    parsed = urlparse(mqtt_url)

    if parsed.scheme not in {"mqtt", "mqtts", "tcp", "ssl"}:
        raise RuntimeError("MQTT_URL must start with mqtt://, mqtts://, tcp://, or ssl://")
    if not parsed.hostname:
        raise RuntimeError("MQTT_URL must include a host")

    mqtt_tls = parsed.scheme in {"mqtts", "ssl"}
    mqtt_qos = _int("MQTT_QOS", 1, minimum=0)
    if mqtt_qos not in {0, 1, 2}:
        raise RuntimeError("MQTT_QOS must be 0, 1, or 2")

    interval_minutes = _float("HEARTBEAT_INTERVAL_MINUTES", 5.0, minimum=0.001)

    return Settings(
        mqtt_url=mqtt_url,
        mqtt_host=parsed.hostname,
        mqtt_port=parsed.port or (8883 if mqtt_tls else 1883),
        mqtt_tls=mqtt_tls,
        mqtt_username=_optional("MQTT_USERNAME"),
        mqtt_password=_optional("MQTT_PASS") or _optional("MQTT_PASSWORD"),
        mqtt_topic=mqtt_topic,
        mqtt_message=os.getenv("MQTT_MESSAGE", "heartbeat"),
        mqtt_qos=mqtt_qos,
        mqtt_retain=_bool("MQTT_RETAIN", False),
        mqtt_keepalive_seconds=_int("MQTT_KEEPALIVE_SECONDS", 30, minimum=1),
        mqtt_connect_timeout_seconds=_float("MQTT_CONNECT_TIMEOUT_SECONDS", 30.0, minimum=0.1),
        mqtt_publish_timeout_seconds=_float("MQTT_PUBLISH_TIMEOUT_SECONDS", 10.0, minimum=0.1),
        mqtt_retry_seconds=_float("MQTT_RETRY_SECONDS", 10.0, minimum=0.1),
        heartbeat_interval_seconds=interval_minutes * 60.0,
        publish_immediately=_bool("HEARTBEAT_PUBLISH_IMMEDIATELY", True),
    )
