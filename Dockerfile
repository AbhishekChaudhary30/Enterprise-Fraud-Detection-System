# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY pyproject.toml requirements.txt README.md ./
COPY src ./src
RUN pip install --upgrade pip && pip install .
COPY configs ./configs
COPY dashboard ./dashboard
COPY scripts ./scripts
COPY reports ./reports
COPY models ./models

FROM base AS production
EXPOSE 8000
CMD ["python", "scripts/start_api.py"]

FROM base AS development
RUN pip install -e ".[dev]"
EXPOSE 8000 8501
CMD ["python", "scripts/start_api.py"]
