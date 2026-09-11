FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml README.md ./
COPY elephantine ./elephantine
RUN uv venv /app/.venv && uv pip install --no-cache -e .
ENV PATH="/app/.venv/bin:"
ENV ELEPHANTINE_STORAGE_DIR="/app/data"
ENV HOST="0.0.0.0"
ENV PORT=8765
EXPOSE 8765
VOLUME ["/app/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD curl -f http://localhost:8765/health || exit 1
CMD ["elephantine", "start", "--host", "0.0.0.0", "--port", "8765"]
