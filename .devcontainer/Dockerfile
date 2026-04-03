FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/root/.local/bin:${PATH}" \
    UV_LINK_MODE=copy

# check uv container

RUN --mount=type=cache,target=/var/cache/apt \
    set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      curl make bash git ca-certificates procps \
    && rm -rf /var/lib/apt/lists/*

# uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /workspace

COPY pyproject.toml ./

# Install dependencies globally
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system pyspark>=4.0.0 minio>=7.1.0 kafka-python-ng>=2.2.2 \
    psycopg2-binary>=2.9.0 redis>=4.5.0 requests>=2.28.0 pandas>=1.5.0 \
    pyarrow>=10.0.0 streamlit>=1.49.1 confluent-kafka>=2.11.1 \
    python-dotenv>=1.1.1 grpcio>=1.74.0 grpcio-status>=1.74.0 \
    apache-airflow-providers-postgres>=5.0.0 apache-airflow-providers-redis>=3.0.0 \
    apache-airflow-providers-apache-spark>=4.0.0 apache-airflow-providers-apache-kafka>=1.0.0 \
    pinotdb pymysql

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
