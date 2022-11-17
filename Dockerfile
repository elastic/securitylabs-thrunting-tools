FROM python:3.11.0-slim-bullseye as base

USER root
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update && \
    apt-get install -y gcc gnupg make curl librdkafka-dev && \
    pip install --upgrade pip && \
    curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin/:$PATH" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=1

FROM base AS builder

USER root

WORKDIR /runtime
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --only main
COPY . .

FROM base as runtime

USER root
COPY --from=builder /runtime /runtime
WORKDIR /
ENV PATH="/runtime/.venv/bin/:${PATH}" \
    CONFIG_PATH="/config.yml"
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    cd /runtime && poetry install --only main
