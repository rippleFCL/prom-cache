FROM python:3.13-slim-bookworm AS requirement-builder

WORKDIR /app

RUN pip install --no-cache-dir poetry poetry-plugin-export

COPY ./pyproject.toml /app
COPY ./poetry.lock /app

RUN poetry export --without-hashes -f requirements.txt --output requirements.txt

FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    ORG_ID= \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=9221

WORKDIR /app

COPY --from=requirement-builder /app/requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt && \
    apt update && \
    apt install -y curl && \
    apt-get clean autoclean && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}

COPY server/ .

EXPOSE 9221

USER 1000:1000

ENTRYPOINT [ "uvicorn", "main:app", "--interface", "wsgi" ]
