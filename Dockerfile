FROM python:3.10-slim

ARG POETRY_HOME=/etc/poetry

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=${POETRY_HOME} python -

ENV PATH="${PATH}:${POETRY_HOME}/bin"

WORKDIR /app

COPY pyproject.toml /app/

RUN poetry config virtualenvs.create false && poetry install

ADD . ./
