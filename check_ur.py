import os
import json
import requests
from bs4 import BeautifulSoup

# データ保存用のファイルパス
DATA_PATH = "previous.json"
NEW_ARRIVALS_PATH = "new_arrivals.json"

# URの新築賃貸住宅一覧を取得する関数
def fetch_ur_listings():
    url = "https://www.ur-net.go.jp/chintai/information/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    base_url = "https://www.ur-net.go.jp"
    links = soup.select("a.item_link.fc_blue.item_cell")

    listings = []
    for link in links:
        text = link.get_text(strip=True)
        href = link.get("href")
        # 「新築賃貸住宅」の文字列を含むリンクだけを抽出
        if "新築賃貸住宅" in text:
            listings.append({"title": text, "url": base_url + href})
    return listings

# 前回保存したデータを読み込む関数
def load_previous():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# JSONデータを指定ファイルに保存する関数
def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 新着や更新情報を検出する関数
def detect_new_listings(current, previous):
    previous_titles = {item["title"] for item in previous}
    new_items = [item for item in current if item["title"] not in previous_titles]

    new_arrivals = []
    updates = []

    for item in new_items:
        title = item["title"]
        if "新規入居者募集" in title:
            new_arrivals.append(item)
        elif any(kw in title for kw in ["抽選募集", "応募状況", "抽選結果"]):
            updates.append(item)

    return new_arrivals, updates

# LINEグループに通知を送る関数
def notify_line(message):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    group_id = os.environ.get("LINE_GROUP_ID")

    if not token or not group_id:
        print("❌ LINE_CHANNEL_ACCESS_TOKEN または LINE_GROUP_ID が設定されていません")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "to": group_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    try:
        res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)
        print(f"📢 LINEグループ通知送信！ステータス: {res.status_code}")
        print(res.text)
    except Exception as e:
        print(f"⚠️ LINEグループ通知に失敗: {e}")

# 通知メッセージを整形する関数
def format_message(header, items):
    lines = [header]
    for item in items:
        lines.append(f"・{item['title']}\n{item['url']}")
    return "\n".join(lines)

# メイン処理
def main():
    current = fetch_ur_listings()           # 現在の物件一覧を取得
    previous = load_previous()              # 前回のデータを読み込み
    new_arrivals, updates = detect_new_listings(current, previous)  # 差分を検出

    print(f"🌿 new_arrivals: {len(new_arrivals)} 件")
    print(f"🌿 updates: {len(updates)} 件")

    if new_arrivals:
        save_json(NEW_ARRIVALS_PATH, new_arrivals)  # 新着を保存
        notify_line(format_message("🔔 新着物件のお知らせ", new_arrivals))  # LINE通知
        save_json(DATA_PATH, current)  # 最新データを保存
    elif updates:
        notify_line(format_message("📄 更新情報のお知らせ", updates))  # LINE通知
        save_json(DATA_PATH, current)  # 最新データを保存
    else:
        print("📭 新着も更新もなし。また明日チェックするね！")

# スクリプトが直接実行されたときだけmain()を呼ぶ
if __name__ == "__main__":
    main()
