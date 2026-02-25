# Zero-Trust Agent — Power Grid Anomaly Detection Pipeline

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV GEMINI_API_KEY=""
ENV LANGSMITH_API_KEY=""
ENV LANGSMITH_PROJECT="zero-trust-agent"
ENV LANGSMITH_TRACING_V2="true"

CMD ["python", "main.py"]
