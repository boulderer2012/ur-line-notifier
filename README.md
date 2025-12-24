# UR LINE Notifier

UR都市機構の新築賃貸住宅情報を定期的にチェックし、LINEグループに新着や更新情報を通知するツールです。  
GitHub Actions を使って自動実行され、Renderなどの外部サービスと連携することも可能です。

---

## 🧭 スクリプトの使い分け

このリポジトリには、UR都市機構の新築賃貸住宅情報をチェックする2つのスクリプトが含まれています。  
それぞれの役割と特徴は以下の通りです：

| スクリプト名 | 特徴 | 使用技術 | 実行環境 | 通知先 |
|--------------|------|----------|----------|--------|
| `check_ur.py` | 軽量・高速。静的HTMLから物件情報を取得 | requests + BeautifulSoup | GitHub Actionsで毎日実行 | LINEグループ |
| `ur_checker.py` | 動的ページ対応。抽選・関東ボタンを自動クリックして情報取得 | Selenium + BeautifulSoup | GitHub Actionsで月1実行（または手動） | LINEグループ |

### 使い分けのイメージ

- **毎日の新着チェック → `check_ur.py`**
- **抽選物件や詳細情報の深掘り → `ur_checker.py`**

どちらも `previous.json` を使って前回との差分を検出し、LINEグループに通知します。

---

## 📄 ur_checker.py について

`ur_checker.py` は、Selenium を使って UR都市機構の新築賃貸住宅ページをブラウザ操作し、  
「抽選」や「関東」などのフィルターを自動でクリックして、より詳細な物件情報を取得・通知するスクリプトです。

### 特徴

- JavaScriptで動的に生成される情報にも対応（Selenium使用）
- 「＃抽選」「＃関東」ボタンを自動クリックして対象物件を抽出
- `check_ur.py` と同様に、前回との差分を検出してLINEグループに通知
- 通知先やトークンは環境変数で管理（`LINE_CHANNEL_ACCESS_TOKEN`, `LINE_GROUP_ID`）

### 実行方法

GitHub Actions で `check_ur.py` と一緒に定期実行されるよう設定されています。  
手動で実行する場合は、以下のように実行できます：

```bash
python ur_checker.py
