FROM python:3.11-slim

WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# ログディレクトリを作成して権限設定
RUN mkdir -p /app/logs && chown -R 1000:1000 /app/logs && chmod 755 /app/logs

EXPOSE 5000

CMD ["python", "app.py"]
