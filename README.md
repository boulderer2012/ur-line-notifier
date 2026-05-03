# URライン通知
![Check and Ping](https://github.com/boulderer2012/ur-line-notifier/actions/workflows/check-and-ping.yml/badge.svg)

UR都市機構の賃貸住宅情報を定期的にチェックし、**LINEグループに新着情報を通知するツール**です。  
GitHub Actions を使って毎日自動実行されます。

---

## 🧭 スクリプトの構成

`ur_checker.py` のみを使用しています。

| 📝 スクリプト名 | 🔍 特徴 | 🛠 使用技術 | ⚙️ 実行環境 | 📲 通知先 |
|---|---|---|---|---|
| `ur_checker.py` | 動的ページ対応。Seleniumでブラウザを自動操作し、BeautifulSoupでHTMLを解析してスクレイピング | Selenium + BeautifulSoup | GitHub Actionsで毎日実行 | LINEグループ |

---

## 📌 監視対象エリア

### 埼玉側（東武東上線・JR武蔵野線）
- 和光市駅 / 朝霞駅 / 朝霞台駅 / 北朝霞駅 / 志木駅

### 東京側
- 大井町駅 / 東十条駅 / 王子駅 / 赤羽駅 / 十条駅 / 池袋駅 / 板橋駅

---

## 📌 差分検出と通知の仕様

- 前回の取得結果は **`previous.json` に保存**されます。
- 次回実行時に **タイトル＋URLのペアで差分を検出**し、**新着物件のみをLINEグループに通知**します。
- **面積60㎡以上**の物件のみを対象とします。
- アクセス情報の**最初の駅名を最寄り駅として通知に表示**します。
- **URLで重複除去**するため、複数駅の検索結果に同じ物件が出ても通知は1回だけです。
- `previous.json` が空（初回実行や手動リセット時）の場合は、**通知せずに保存のみを行い、誤通知を防止**します。

---

## 🛠 使用技術

| 技術 | 用途 |
|---|---|
| Selenium | ブラウザを自動操作してJavaScriptで動的に生成されるページを取得（スクレイピング） |
| WebDriverWait | 物件カードが表示されるまでの賢い待機処理 |
| BeautifulSoup | 取得したHTMLを解析して物件情報を抽出（スクレイピング） |
| requests | LINE Messaging API呼び出し |
| 正規表現（re） | 駅名・面積の抽出・アクセス情報の整形 |
| json | previous.jsonの読み書きによる差分管理 |
| 環境変数（dotenv） | LINEトークンをコードに直書きせず安全に管理 |
| 重複除去（seen_urls） | 複数駅で同じ物件が出ても通知は1回だけ |
| pytz | タイムゾーン変換（UTC→JST）で正確な時刻表示 |

> ⚠️ 本ツールはURサイトのAPIは使用せず、SeleniumとBeautifulSoupを用いたスクレイピングで情報を取得しています。個人利用目的のみで使用してください。

---

## 🔐 環境変数の設定

LINE通知に必要な情報を環境変数で管理しています。  
`.env` は `.gitignore` に追加されており、GitHubにはアップロードされません。

`.env.example` をコピーして `.env` を作成し、以下を記述してください：

```env
LINE_CHANNEL_ACCESS_TOKEN=あなたのLINEチャネルアクセストークン
LINE_GROUP_ID=通知を送りたいグループのID
```

GitHub Actionsで使用する場合は、リポジトリの **Settings → Secrets** に同じキーを登録してください。

---

## 🚀 実行方法

GitHub Actions により毎日10:12（JST）に自動実行されます。

手動実行する場合：

```bash
python ur_checker.py
```
