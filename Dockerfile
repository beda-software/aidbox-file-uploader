FROM python:3.12-slim AS base

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* \
    && addgroup --gid 1000 dockeruser \
    && adduser --disabled-login --uid 1000 --gid 1000 dockeruser

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# The runtime image is built from this stage, so the type check gates every build.
FROM base AS dev

ENV POETRY_VIRTUALENVS_CREATE=false

RUN pip install poetry \
    && python -m venv $VIRTUAL_ENV \
    && mkdir -p /app \
    && chown -R dockeruser:dockeruser $VIRTUAL_ENV /app

USER dockeruser
WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY . .
RUN poetry run mypy

FROM dev AS runtime-deps

RUN poetry sync --only main --no-root \
    && pip uninstall -y pip

FROM base AS runtime

RUN pip uninstall -y pip

COPY --from=runtime-deps --chown=root:root $VIRTUAL_ENV $VIRTUAL_ENV
WORKDIR /app
COPY main.py ./
COPY app/ app/

USER dockeruser
CMD ["gunicorn", "main:create_gunicorn_app", "--worker-class", "aiohttp.worker.GunicornWebWorker", "-b", "0.0.0.0:8081"]
