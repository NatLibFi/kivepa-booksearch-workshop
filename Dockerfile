FROM python:3.8-slim-bookworm


RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip setuptools wheel flask elasticsearch requests gunicorn

RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

WORKDIR /app
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser templates/ templates/
COPY --chown=appuser:appuser static/ static/
RUN mkdir /app/sqlite3-data
VOLUME /app/sqlite3-data

CMD gunicorn app:app
