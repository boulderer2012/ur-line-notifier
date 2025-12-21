import os
import json
import requests
from bs4 import BeautifulSoup

DATA_PATH = "previous.json"
NEW_ARRIVALS_PATH = "new_arrivals.json"
UPDATES_PATH = "updates.json"

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
        if "新築賃貸住宅" in text:
            listings.append({"title": text, "url": base_url + href})
    return listings

def load_previous():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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

def ping_render():
    render_url = os.environ.get("RENDER_WEBHOOK_URL")
    if not render_url:
        print("❌ RENDER_WEBHOOK_URL が設定されていません")
        return
    try:
        res = requests.get(render_url)
        print(f"🚀 Render起動リクエスト送信！ステータス: {res.status_code}")
    except Exception as e:
        print(f"⚠️ Render起動に失敗: {e}")

def notify_line(message):
    token = os.environ.get("LINE_NOTIFY_TOKEN")
    if not token:
        print("❌ LINE_NOTIFY_TOKEN が設定されていません")
        return
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "message": message
    }
    try:
        res = requests.post("https://notify-api.line.me/api/notify", headers=headers, data=data)
        print(f"📩 LINE通知送信！ステータス: {res.status_code}")
    except Exception as e:
        print(f"⚠️ LINE通知に失敗: {e}")

def format_message(header, items):
    lines = [header]
    for item in items:
        lines.append(f"・{item['title']}\n{item['url']}")
    return "\n".join(lines)

def main():
    current = fetch_ur_listings()
    previous = load_previous()
    new_arrivals, updates = detect_new_listings(current, previous)

    if new_arrivals:
        print(f"🔔 新着物件 {len(new_arrivals)} 件検出！Renderを起動します！")
        for item in new_arrivals:
            print(f"・{item['title']}")
        save_json(NEW_ARRIVALS_PATH, new_arrivals)
        notify_line(format_message("🔔 新着物件のお知らせ", new_arrivals))
        ping_render()
        save_json(DATA_PATH, current)
    elif updates:
        print(f"📄 更新情報 {len(updates)} 件ありました（Renderは起動しません）")
        for item in updates:
            print(f"・{item['title']}")
        save_json(UPDATES_PATH, updates)
        notify_line(format_message("📄 更新情報のお知らせ", updates))
        save_json(DATA_PATH, current)
    else:
        print("📭 新着なし。Renderは起動しません。")

if __name__ == "__main__":
    main()
