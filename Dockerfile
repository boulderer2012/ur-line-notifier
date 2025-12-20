FROM selenium/standalone-chrome:latest

USER root

# Pythonと必要なツールをインストール
RUN apt-get update && apt-get install -y python3 python3-pip

# 作業ディレクトリ
WORKDIR /app

# ファイルをコピー
COPY . .

# 依存関係をインストール
RUN pip3 install --no-cache-dir -r requirements.txt

# スクリプトを実行
CMD ["python3", "ur_checker.py"]
