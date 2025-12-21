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
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")
    group_id = os.environ.get("LINE_GROUP_ID")

    if not token:
        print("❌ トークン未設定")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    for target, name in [(user_id, "個人"), (group_id, "グループ")]:
        if not target:
            print(f"⚠️ {name}ID未設定")
            continue
        data = {
            "to": target,
            "messages": [
                {
                    "type": "text",
                    "text": f"{name}宛てテスト通知です📩"
                }
            ]
        }
        res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)
        print(f"📩 {name}通知ステータス: {res.status_code}")
        print(res.text)

def format_message(header, items):
    lines = [header]
    for item in items:
        lines.append(f"・{item['title']}\n{item['url']}")
    return "\n".join(lines)

def main():
    # current = fetch_ur_listings()
    current = [
        # 新着物件（新規入居者募集）
        {
            "title": "新築賃貸住宅「テストヒルズ」新規入居者募集について",
            "url": "https://example.com/new"
        },
        # 更新情報（抽選結果）
        {
            "title": "新築賃貸住宅「テストタワー」抽選結果について（抽選日:12/20）",
            "url": "https://example.com/update"
        },
        # すでにあるデータ（無視されるはず）
        {
            "title": "新築賃貸住宅「テストタワー」抽選募集について（令和7年12月1日時点）",
            "url": "https://example.com/old"
        }
    ]

    previous = load_previous()
    new_arrivals, updates = detect_new_listings(current, previous)

    print(f"🧪 new_arrivals: {len(new_arrivals)} 件")
    print(f"🧪 updates: {len(updates)} 件")

    if new_arrivals:
        save_json(NEW_ARRIVALS_PATH, new_arrivals)
        notify_line(format_message("🔔 新着物件のお知らせ", new_arrivals))
        ping_render()
        save_json(DATA_PATH, current)
    elif updates:
        save_json(UPDATES_PATH, updates)
        notify_line(format_message("📄 更新情報のお知らせ", updates))
        save_json(DATA_PATH, current)
    else:
        print("📭 新着なし。Renderは起動しません。")

if __name__ == "__main__":
    main()
