# HeartbeatMQTT

HeartbeatMQTT is a small, reliable MQTT heartbeat publisher managed with Astral uv. It publishes a configurable message to a configurable MQTT topic every X minutes and can run directly with uv/uvx or as a long-running Docker container.

## Environment variables

Required:

| Variable | Description |
| --- | --- |
| `MQTT_URL` | Broker URL. Supports `mqtt://`, `tcp://`, `mqtts://`, and `ssl://`. |
| `MQTT_TOPIC` | Topic that receives the heartbeat. |

Common optional settings:

| Variable | Default | Description |
| --- | --- | --- |
| `MQTT_MESSAGE` | `heartbeat` | Payload sent each interval. |
| `HEARTBEAT_INTERVAL_MINUTES` | `5` | Minutes between successful heartbeat publishes. Decimals are allowed. |
| `MQTT_USERNAME` | empty | MQTT username. |
| `MQTT_PASSWORD` | empty | MQTT password. `MQTT_PASS` is also accepted. |
| `MQTT_QOS` | `1` | MQTT QoS: 0, 1, or 2. |
| `MQTT_RETAIN` | `false` | Publish retained messages. |
| `HEARTBEAT_PUBLISH_IMMEDIATELY` | `true` | Publish once immediately at startup. |
| `MQTT_RETRY_SECONDS` | `10` | Delay before retrying a failed/deferred publish. |

Additional tuning variables are shown in `.env.example`.

## Reliability behavior

- Uses paho-mqtt's network loop and reconnect backoff.
- Waits for broker connectivity before publishing.
- Retries failed/deferred publishes on `MQTT_RETRY_SECONDS` rather than waiting a full heartbeat interval.
- Starts the next heartbeat interval after a successful publish.
- Handles SIGTERM and SIGINT for clean container shutdown.
- Docker Compose uses `restart: unless-stopped` and `init: true`.
- Logging goes to stdout/stderr for container log collection.

## Run with uv

```bash
cp .env.example .env
set -a
. ./.env
set +a

uv sync
uv run heartbeatmqtt
```

You can also run from GitHub with uvx:

```bash
uvx --from git+https://github.com/mbush91/HeartbeatMQTT heartbeatmqtt
```

## Run from Docker Hub

```bash
docker run -d \
  --name heartbeatmqtt \
  --restart unless-stopped \
  --env-file .env \
  mbush91/heartbeatmqtt:latest
```

Or use Compose:

```bash
cp .env.example .env
# edit .env
docker compose up -d
```

## Docker Hub publishing

The `Docker Hub Publish` GitHub Actions workflow builds on every push to `main`, semver tag, and manual run. When the repository secrets are configured, it pushes:

- `latest` from the default branch
- `sha-<commit>`
- semver tags such as `0.1.0` and `0.1`

Configure these repository secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

The image is published as `mbush91/heartbeatmqtt` when `DOCKERHUB_USERNAME=mbush91`.

## Development

```bash
uv sync
uv run ruff check .
uv run pytest
uv build
```

## License

MIT
