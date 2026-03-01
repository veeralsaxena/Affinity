FROM python:3.12-slim

WORKDIR /app

# Install system deps for psycopg2 and Playwright
RUN apt-get update && apt-get install -y gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser for WhatsApp automation
RUN playwright install --with-deps chromium

COPY . .

# Exclude local venv / session data
RUN rm -rf venv __pycache__ whatsapp_session

EXPOSE 8000

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
