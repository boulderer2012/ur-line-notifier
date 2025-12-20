FROM python:3.10-slim

# 必要なパッケージをインストール（chromiumとchromedriverを含む）
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    wget \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# ChromeとChromeDriverのパスを確認して環境変数に設定
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 作業ディレクトリ
WORKDIR /app

# ファイルをコピー
COPY . .

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# スクリプトを実行
CMD ["python", "ur_checker.py"]

