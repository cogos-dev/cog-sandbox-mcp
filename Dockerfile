FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    COG_SANDBOX_ROOT=/workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1001 sandbox \
    && useradd --uid 1001 --gid sandbox --no-create-home sandbox

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

RUN mkdir -p /workspace && chown sandbox:sandbox /workspace

USER sandbox
WORKDIR /workspace

ENTRYPOINT ["python", "-u", "-m", "cog_sandbox_mcp"]
