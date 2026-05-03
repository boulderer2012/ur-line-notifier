import os
import json
import time
import requests
import pytz
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = "previous.json"

def load_previous():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_current(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
GROUP_ID = os.environ.get("LINE_GROUP_ID")

def send_line_message(message):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    body = {
        'to': GROUP_ID,
        'messages': [{'type': 'text', 'text': message}]
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    print(f'📤 ステータスコード: {response.status_code}')
    print(f'📨 レスポンス: {response.text}')

def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

def is_size_ok(size_str):
    try:
        return float(size_str.replace("㎡", "").strip()) >= 60.0
    except:
        return False

# 🔹 路線・駅URLから物件を取得する汎用関数
def fetch_listings_from_url(search_url, label=""):
    driver = create_driver()
    driver.get(search_url)

    # 物件リストが読み込まれるまで待機
    wait = WebDriverWait(driver, 30)
    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bukken_list")))
        time.sleep(3)
    except:
        print(f"⚠️ [{label}] 物件リスト読み込みタイムアウト（空き物件なしの可能性）")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    listings = []
    base_url = "https://www.ur-net.go.jp"
    cards = soup.select("li.bukken_list")

    print(f"🔍 [{label}] 取得した物件数: {len(cards)}")

    for card in cards:
        name_tag = card.select_one("p.property_name")
        if not name_tag:
            continue

        detail_link = card.select_one("a")
        if not detail_link:
            continue

        href = detail_link.get("href", "")
        full_url = base_url + href if href.startswith("/") else href
        title = name_tag.text.strip()

        size = card.select_one("p.size")
        size_text = size.text.strip() if size else ""

        if not is_size_ok(size_text):
            continue

        layout = card.select_one("p.layout")
        floor = card.select_one("p.floor")
        layout_text = layout.text.strip() if layout else ""
        floor_text = floor.text.strip() if floor else ""

        listings.append({
            "title": f"[{label}] {title} {layout_text} {size_text} {floor_text}",
            "url": full_url
        })

    print(f"✅ [{label}] 条件一致: {len(listings)}件")
    return listings

# 🔹 全対象エリアから物件を取得
def fetch_all_listings():
    targets = [
        ("https://www.ur-net.go.jp/chintai/kanto/tokyo/result/?line=3600&todofuken=tokyo", "JR京浜東北線"),
        ("https://www.ur-net.go.jp/chintai/kanto/tokyo/result/?line=5300&todofuken=tokyo", "JR山手線"),
        ("https://www.ur-net.go.jp/chintai/kanto/tokyo/result/?line=56800&todofuken=tokyo", "東京メトロ副都心線"),
        ("https://www.ur-net.go.jp/chintai/kanto/saitama/result/?line_station=14400_1487&todofuken=saitama", "和光市駅"),
        ("https://www.ur-net.go.jp/chintai/kanto/saitama/result/?line_station=14400_1489&todofuken=saitama", "朝霞駅"),
        ("https://www.ur-net.go.jp/chintai/kanto/saitama/result/?line_station=14400_1488&todofuken=saitama", "東朝霞駅"),
        ("https://www.ur-net.go.jp/chintai/kanto/saitama/result/?line_station=14400_1490&todofuken=saitama", "北朝霞駅"),
    ]

    all_listings = []
    for url, label in targets:
        listings = fetch_listings_from_url(url, label)
        all_listings += listings

    return all_listings

# 🔹 UR公式お知らせページから新築物件を取得
def fetch_ur_news_listings():
    url = "https://www.ur-net.go.jp/chintai/information/"
    driver = create_driver()
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    try:
        lottery_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '＃抽選')]")))
        lottery_button.click()
    except:
        print("抽選ボタンのクリックに失敗")

    try:
        kanto_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '＃関東')]")))
        kanto_button.click()
    except:
        print("関東ボタンのクリックに失敗")

    time.sleep(3)
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, "html.parser")
    base_url = "https://www.ur-net.go.jp"
    links = soup.select("a.item_link.fc_blue.item_cell")

    listings = []
    for link in links:
        text = link.get_text(strip=True)
        href = link.get("href")
        if "新築賃貸住宅" in text:
            listings.append({"title": f"[新築] {text}", "url": base_url + href})

    return listings

def detect_new_listings(current, previous):
    previous_set = {(item["title"], item["url"]) for item in previous}
    return [item for item in current if (item["title"], item["url"]) not in previous_set]

def main():
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    print(f"🕒 チェック実行時刻（JST）: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    current = fetch_ur_news_listings() + fetch_all_listings()
    previous = load_previous()

    if not previous:
        print("📂 初回実行のため、通知せず保存のみ行います。")
        save_current(current)
        return

    new_list = detect_new_listings(current, previous)
    MAX_ITEMS = 5

    if new_list:
        print(f"🔔 {len(new_list)} 件の新着物件を検出！")
        message = f"🏠 新着物件（{now.strftime('%Y/%m/%d %H:%M')} 時点）\n\n"
        for item in new_list[:MAX_ITEMS]:
            message += f"{item['title']}\n{item['url']}\n\n"
        send_line_message(message.strip())
    else:
        print("📭 新着なし〜")

    save_current(current)

if __name__ == "__main__":
    main()
