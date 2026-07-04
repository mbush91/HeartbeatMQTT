from __future__ import annotations

import logging
import threading
from typing import Protocol

import paho.mqtt.client as mqtt

from .config import Settings

LOGGER = logging.getLogger(__name__)


class PublishInfo(Protocol):
    rc: int
    mid: int

    def wait_for_publish(self, timeout: float | None = None) -> None: ...

    def is_published(self) -> bool: ...


class MqttClient(Protocol):
    def username_pw_set(self, username: str, password: str | None = None) -> None: ...
    def tls_set(self, *args: object, **kwargs: object) -> None: ...
    def reconnect_delay_set(self, min_delay: int = 1, max_delay: int = 120) -> None: ...
    def connect_async(self, host: str, port: int = 1883, keepalive: int = 60) -> int: ...
    def loop_start(self) -> int: ...
    def loop_stop(self) -> int: ...
    def disconnect(self) -> int: ...

    def publish(
        self,
        topic: str,
        payload: str | bytes | None = None,
        qos: int = 0,
        retain: bool = False,
    ) -> PublishInfo: ...


class HeartbeatPublisher:
    def __init__(self, settings: Settings, client: MqttClient | None = None) -> None:
        self.settings = settings
        self._connected = threading.Event()
        self._client = client or mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._configure_client()

    def _configure_client(self) -> None:
        if self.settings.mqtt_username is not None:
            self._client.username_pw_set(
                self.settings.mqtt_username,
                self.settings.mqtt_password,
            )
        if self.settings.mqtt_tls:
            self._client.tls_set()

        self._client.reconnect_delay_set(min_delay=1, max_delay=60)
        self._client.on_connect = self._on_connect  # type: ignore[attr-defined]
        self._client.on_disconnect = self._on_disconnect  # type: ignore[attr-defined]

    def _on_connect(
        self,
        _client: mqtt.Client,
        _userdata: object,
        _flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None,
    ) -> None:
        if reason_code == 0:
            LOGGER.info(
                "Connected to MQTT broker %s:%s",
                self.settings.mqtt_host,
                self.settings.mqtt_port,
            )
            self._connected.set()
        else:
            self._connected.clear()
            LOGGER.error("MQTT connection rejected: %s", reason_code)

    def _on_disconnect(
        self,
        _client: mqtt.Client,
        _userdata: object,
        _disconnect_flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None,
    ) -> None:
        self._connected.clear()
        LOGGER.warning("Disconnected from MQTT broker: %s", reason_code)

    def start(self) -> None:
        result = self._client.connect_async(
            self.settings.mqtt_host,
            self.settings.mqtt_port,
            keepalive=self.settings.mqtt_keepalive_seconds,
        )
        if result != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT connect_async failed with rc={result}")
        self._client.loop_start()

    def stop(self) -> None:
        self._connected.clear()
        try:
            self._client.disconnect()
        finally:
            self._client.loop_stop()

    def publish_once(self) -> bool:
        if not self._connected.wait(timeout=self.settings.mqtt_connect_timeout_seconds):
            LOGGER.warning("MQTT broker is not connected; heartbeat publish deferred")
            return False

        try:
            info = self._client.publish(
                self.settings.mqtt_topic,
                self.settings.mqtt_message,
                qos=self.settings.mqtt_qos,
                retain=self.settings.mqtt_retain,
            )
            info.wait_for_publish(timeout=self.settings.mqtt_publish_timeout_seconds)
        except (RuntimeError, ValueError) as exc:
            LOGGER.warning("MQTT publish failed: %s", exc)
            return False

        if info.rc != mqtt.MQTT_ERR_SUCCESS or not info.is_published():
            LOGGER.warning("MQTT publish did not complete successfully: rc=%s", info.rc)
            return False

        LOGGER.info(
            "Published heartbeat mid=%s topic=%s qos=%s retain=%s",
            info.mid,
            self.settings.mqtt_topic,
            self.settings.mqtt_qos,
            self.settings.mqtt_retain,
        )
        return True
