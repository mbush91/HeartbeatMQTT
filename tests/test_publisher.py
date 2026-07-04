from heartbeatmqtt.config import Settings
from heartbeatmqtt.publisher import HeartbeatPublisher


class FakePublishInfo:
    rc = 0
    mid = 42

    def __init__(self, published=True):
        self._published = published
        self.timeout = None

    def wait_for_publish(self, timeout=None):
        self.timeout = timeout

    def is_published(self):
        return self._published


class FakeClient:
    def __init__(self):
        self.calls = []
        self.on_connect = None
        self.on_disconnect = None
        self.publish_info = FakePublishInfo()

    def username_pw_set(self, username, password=None):
        self.calls.append(("username_pw_set", username, password))

    def tls_set(self, *args, **kwargs):
        self.calls.append(("tls_set",))

    def reconnect_delay_set(self, min_delay=1, max_delay=120):
        self.calls.append(("reconnect_delay_set", min_delay, max_delay))

    def connect_async(self, host, port=1883, keepalive=60):
        self.calls.append(("connect_async", host, port, keepalive))
        return None

    def loop_start(self):
        self.calls.append(("loop_start",))
        return 0

    def loop_stop(self):
        self.calls.append(("loop_stop",))
        return 0

    def disconnect(self):
        self.calls.append(("disconnect",))
        return 0

    def publish(self, topic, payload=None, qos=0, retain=False):
        self.calls.append(("publish", topic, payload, qos, retain))
        return self.publish_info


def make_settings():
    return Settings(
        mqtt_url="mqtt://broker.local:1883",
        mqtt_host="broker.local",
        mqtt_port=1883,
        mqtt_tls=False,
        mqtt_username="user",
        mqtt_password="secret",
        mqtt_topic="devices/heartbeat",
        mqtt_message="alive",
        mqtt_qos=1,
        mqtt_retain=False,
        mqtt_keepalive_seconds=30,
        mqtt_connect_timeout_seconds=0.01,
        mqtt_publish_timeout_seconds=10.0,
        mqtt_retry_seconds=1.0,
        heartbeat_interval_seconds=60.0,
        publish_immediately=True,
    )


def test_start_accepts_connect_async_none_return():
    fake = FakeClient()
    publisher = HeartbeatPublisher(make_settings(), client=fake)

    publisher.start()

    assert ("connect_async", "broker.local", 1883, 30) in fake.calls
    assert ("loop_start",) in fake.calls


def test_publish_once_when_connected():
    fake = FakeClient()
    publisher = HeartbeatPublisher(make_settings(), client=fake)
    publisher._connected.set()

    assert publisher.publish_once() is True
    assert ("publish", "devices/heartbeat", "alive", 1, False) in fake.calls
    assert fake.publish_info.timeout == 10.0


def test_publish_once_defers_when_disconnected():
    fake = FakeClient()
    publisher = HeartbeatPublisher(make_settings(), client=fake)

    assert publisher.publish_once() is False
    assert not any(call[0] == "publish" for call in fake.calls)
