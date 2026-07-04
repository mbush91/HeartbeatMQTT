FROM ghcr.io/astral-sh/uv:0.11.26-python3.12-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_DEV=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml README.md ./
RUN uv sync --no-install-project

COPY src ./src
RUN uv sync

ENV PATH="/app/.venv/bin:$PATH"

USER nobody

CMD ["heartbeatmqtt"]
