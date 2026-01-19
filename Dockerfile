FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir -U pip

COPY pyproject.toml /app/
COPY src /app/src

RUN pip install --no-cache-dir -e ".[api]"

EXPOSE 8000

CMD ["uvicorn", "billing_core.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
