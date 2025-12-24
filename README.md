# UR Line Notifier

UR賃貸住宅の空き情報を定期的にチェックし、LINEに通知するツールです。

## 🔧 機能概要

- UR賃貸の空き情報を定期取得
- 条件に合う物件が見つかったらLINEに通知
- GitHub Actionsで自動実行
- Docker対応（任意でローカル実行も可能）

## 🚀 使い方

### 1. 必要な環境変数の設定

以下の環境変数を設定してください：

- `LINE_NOTIFY_TOKEN`：LINE Notifyのアクセストークン

### 2. GitHub Actionsでの自動実行

`.github/workflows/` 以下にあるワークフローが、定期的にスクリプトを実行します。

### 3. ローカルでの実行（任意）

```bash
pip install -r requirements.txt
python check_ur.py
