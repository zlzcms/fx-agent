# Select the image to build based on SERVER_TYPE, defaulting to fastapi_server, or docker-compose build args
ARG SERVER_TYPE=fastapi_server

# === Python environment from uv ===
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Used for build Python packages
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /fba

WORKDIR /fba

# Configure uv environment
ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

# Install dependencies with cache (including server group for wait-for-it)
# Set longer timeout for downloading packages and add retry mechanism
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_HTTP_TIMEOUT=180 \
    UV_CONCURRENT_DOWNLOADS=5 \
    uv sync --frozen --no-dev --group server || \
    (echo "First attempt failed, retrying with increased timeout..." && \
     UV_HTTP_TIMEOUT=300 UV_CONCURRENT_DOWNLOADS=3 \
     uv sync --frozen --no-dev --group server)

# === Runtime base server image ===
FROM python:3.12-slim AS base_server

SHELL ["/bin/bash", "-c"]

# Use more stable mirror sources and install supervisor with timezone support
# Also install WeasyPrint system dependencies (Cairo, Pango, etc.) and Chinese fonts
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        supervisor \
        tzdata \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        shared-mime-info \
        fonts-noto-cjk \
        fonts-wqy-zenhei \
        fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# Set timezone to Asia/Shanghai
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY . /fba

COPY --from=builder /usr/local /usr/local

# Install plugin dependencies
WORKDIR /fba
ENV PYTHONPATH=/fba
# RUN python3 backend/scripts/init_plugin.py

# 确保所有脚本都有执行权限
RUN chmod +x /fba/scripts/database/*.sh /fba/scripts/*.sh /fba/scripts/deployment/*.sh

# === FastAPI server image ===
FROM base_server AS fastapi_server

WORKDIR /fba

COPY scripts/deployment/config/supervisord.conf /etc/supervisor/supervisord.conf
COPY scripts/deployment/config/fastapi_server.conf /etc/supervisor/conf.d/

RUN mkdir -p /var/log/fastapi_server

# wait-for-it is already installed via uv dependencies

EXPOSE 8000

CMD ["/fba/scripts/deployment/start.sh"]

# === Celery server image ===
FROM base_server AS celery

WORKDIR /fba/backend

COPY scripts/deployment/config/supervisord.conf /etc/supervisor/supervisord.conf
COPY scripts/deployment/config/celery.conf /etc/supervisor/conf.d/

RUN mkdir -p /var/log/celery

RUN chmod +x /fba/scripts/deployment/celery.sh

EXPOSE 8555

CMD ["/fba/scripts/deployment/celery.sh"]

# Build image
FROM ${SERVER_TYPE}
