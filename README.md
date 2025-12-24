# UR Line Notifier

UR賃貸住宅の空き情報を定期的にチェックし、LINEに通知するツールです。

## 🔧 機能概要

- UR都市機構の「新築賃貸住宅」ページを定期的にチェック
- 前回取得した物件情報（`previous.json`）と比較し、**新着物件**や**更新情報（抽選・応募状況など）**を検出
- 新着があれば `new_arrivals.json` に保存し、LINEグループに通知
- 通知には LINE Messaging API を使用（アクセストークンとグループIDが必要）
- 実行後、最新の物件情報を `previous.json` に保存して次回比較に備える


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
