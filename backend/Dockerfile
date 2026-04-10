#------------BUILDER-------------
FROM python:3.12 AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY app.py .

#---------RUNNER----------------
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local

COPY app.py .

RUN useradd -m appuser

USER appuser

EXPOSE 8000

CMD [ "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000" ]