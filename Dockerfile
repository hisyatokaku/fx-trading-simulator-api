FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
# ワーカー数は UVICORN_WORKERS 環境変数で調整（既定 2 = 現行 e2-medium の 2 vCPU 分）。
# VM をスケールアップしたら vCPU 数に合わせて上げる（compose の environment か -e で指定）。
# shell 形式にして環境変数を展開する。
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}
