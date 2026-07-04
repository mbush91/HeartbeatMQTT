from __future__ import annotations

import logging
import signal
import threading

from .config import Settings, load_settings
from .publisher import HeartbeatPublisher

LOGGER = logging.getLogger(__name__)


def run(settings: Settings, stop_event: threading.Event | None = None) -> None:
    stop_event = stop_event or threading.Event()
    publisher = HeartbeatPublisher(settings)
    publisher.start()

    try:
        if not settings.publish_immediately:
            stop_event.wait(settings.heartbeat_interval_seconds)

        while not stop_event.is_set():
            if publisher.publish_once():
                stop_event.wait(settings.heartbeat_interval_seconds)
            else:
                stop_event.wait(settings.mqtt_retry_seconds)
    finally:
        LOGGER.info("Stopping HeartbeatMQTT")
        publisher.stop()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = load_settings()
    stop_event = threading.Event()

    def request_stop(signum: int, _frame: object) -> None:
        LOGGER.info("Received signal %s; shutting down", signum)
        stop_event.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    LOGGER.info(
        "Starting HeartbeatMQTT topic=%s interval=%.3f minutes",
        settings.mqtt_topic,
        settings.heartbeat_interval_seconds / 60.0,
    )
    run(settings, stop_event)


if __name__ == "__main__":
    main()
