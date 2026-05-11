# =============================================
# MJ-Agent — Phase 1 sub 1.H production image
#
# Pattern mirrors mj-system v3.2.2 Dockerfile:
#   - Python 3.13-slim
#   - uv for dep install (frozen lockfile in builder)
#   - non-root appuser (uid 1000)
#   - Asia/Shanghai TZ
#   - multi-stage: builder (compile deps) -> runtime (slim)
#
# Entry: mj-agent serve  (Chainlit on $CHAINLIT_PORT, default 8000)
# Healthcheck: mj-agent check
#
# Build:  docker build -f infra/docker/Dockerfile -t mj-agent:0.1 .
# Run:    docker run --rm -p 8001:8000 --env-file .env mj-agent:0.1
# =============================================

# ========== Builder ==========
# Pinned to digest for supply-chain hardening (same pattern as PR #51 for
# CI actions). Dependabot's `docker` ecosystem (.github/dependabot.yml)
# bumps both the digest AND the `# 3.13-slim` tag comment when upstream
# publishes new images.
FROM python:3.14-slim@sha256:1697e8e8d39bf168e177ac6b5fdab6df86d81cfc24dae17dfb96cfc3ef76b4dd AS builder
# tag: 3.13-slim

# Default apt mirror = tuna; avoids Fastly anycast flakiness affecting
# mainland builds (see plans/[PLAN]_dockerfile_apt_mirror_tuna.md). Override
# at build time: --build-arg APT_MIRROR_URL=deb.debian.org
ARG APT_MIRROR_URL=mirrors.tuna.tsinghua.edu.cn

RUN sed -i "s|deb.debian.org|${APT_MIRROR_URL}|g" \
        /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
        gcc libc6-dev libpq-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Layer 1: deps only (re-runs only when pyproject.toml / uv.lock changes).
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Layer 2: project source (re-runs only when src/ changes). Installing the
# project here puts the `mj-agent` console script (defined in
# pyproject.toml [project.scripts]) into /app/.venv/bin/ so the runtime
# stage can call it on PATH.
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# ========== Runtime ==========
FROM python:3.14-slim@sha256:1697e8e8d39bf168e177ac6b5fdab6df86d81cfc24dae17dfb96cfc3ef76b4dd
# tag: 3.13-slim

# ARG redeclare — Docker ARG scope is per FROM; builder default not inherited.
ARG APT_MIRROR_URL=mirrors.tuna.tsinghua.edu.cn

# libpq5 = analyst psycopg client; tini = PID-1 signal handling.
RUN sed -i "s|deb.debian.org|${APT_MIRROR_URL}|g" \
        /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
        libpq5 tini \
    && rm -rf /var/lib/apt/lists/*

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --create-home appuser

WORKDIR /app

LABEL com.mj-agent.service="agent" \
      com.mj-agent.phase="1" \
      com.mj-agent.description="MJ-Agent — biz-domain data analyst LLM agent"

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/README.md /app/README.md

# config/ is the analyst customer codebook + secrets.enc dir; secrets.enc is
# excluded by .dockerignore (orchestrator injects via env). The codebook
# itself is shipped (it's a YAML codename map; ADR-014).
COPY config/ ./config/
COPY infra/docker/entrypoint.sh /app/entrypoint.sh

# Chart / Excel artifact tmpdir (override with MJ_AGENT_CHART_TMPDIR).
RUN mkdir -p /var/lib/mj-agent/charts && \
    chown -R appuser:appuser /app /var/lib/mj-agent && \
    chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    MJ_AGENT_CHART_TMPDIR=/var/lib/mj-agent/charts

# Container-friendly defaults — bind to 0.0.0.0 so the published port works.
ENV CHAINLIT_HOST=0.0.0.0 \
    CHAINLIT_PORT=8000

USER appuser

EXPOSE 8000

# Healthcheck reuses `mj-agent check` (probes biz DB + Ark + memory DB; ADR-006
# / ADR-009 boundaries enforced at the same layers as the running serve).
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD mj-agent check || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/app/entrypoint.sh"]
CMD ["serve"]
