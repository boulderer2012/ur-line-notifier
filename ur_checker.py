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
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    return driver

def format_access(access_text):
    access_text = re.sub(r'※.*', '', access_text).strip()
    lines = re.split(r'(?=東武|JR|東京メトロ|西武|京急|都営|小田急|京王|東急|相鉄|つくば)', access_text)
    lines = [l.strip() for l in lines if l.strip()]
    return '\n'.join(lines)

def extract_nearest_station(access_text):
    match = re.search(r'「(.+?)」駅', access_text)
    if match:
        return match.group(1) + "駅"
    return None

def is_size_ok(size_str):
    try:
        size = re.search(r"[\d.]+", size_str)
        if size:
            return float(size.group()) >= 60.0
    except:
        pass
    return False

def fetch_listings_from_url(search_url, label=""):
    driver = create_driver()
    try:
        driver.get(search_url)
        time.sleep(8)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "module_cassettes_property"))
            )
        except:
            print(f"📭 [{label}] 空き物件なし")
            return []

        html = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.module_cassettes_property")
    print(f"🔍 [{label}] 取得した物件数: {len(cards)}")

    # デバッグ：最初の1件のステータス情報を出力
    if cards:
        status_tag = cards[0].select_one("div.cassettes_property_status")
        print(f"=== ステータス情報 ===")
        print(status_tag)

    listings = []
    base_url = "https://www.ur-net.go.jp"

    for card in cards:
        name_tag = card.select_one("div.cassettes_property_information p, h2, h3")
        if not name_tag:
            continue
        title = name_tag.get_text(strip=True)
        if not title or len(title) < 2:
            continue

        detail_link = card.select_one("a")
        if not detail_link:
            continue
        href = detail_link.get("href", "")
        full_url = base_url + href if href.startswith("/") else href

        access_tags = card.select("div.cassettes_property_information li")
        access_text = access_tags[0].get_text(strip=True) if access_tags else ""

        info_tag = card.select_one("div.cassettes_property_infolistwrapper")
        info_text = info_tag.get_text(strip=True) if info_tag else ""
        size_match = re.search(r"([\d.]+)\s*㎡", info_text)
        if size_match:
            if float(size_match.group(1)) < 60.0:
                continue

        nearest = extract_nearest_station(access_text)
        station_label = nearest if nearest else label

        listings.append({
            "title": f"[{station_label}] {title}",
            "url": full_url,
            "access": access_text
        })

    print(f"✅ [{label}] 条件一致: {len(listings)}件")
    return listings

def fetch_all_listings():
    # デバッグ用に1駅だけ
    targets = [
    ("https://www.ur-net.go.jp/chintai/kanto/saitama/result/?line_station=14400_2225&todofuken=saitama", "志木駅"),
    ]

    all_listings = []
    seen_urls = set()

    for url, label in targets:
        listings = fetch_listings_from_url(url, label)
        for item in listings:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_listings.append(item)

    return all_listings

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
            listings.append({
                "title": f"[新築] {text}",
                "url": base_url + href,
                "access": ""
            })

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
            message += f"{item['title']}\n"
            if item.get('access'):
                formatted = format_access(item['access'])
                message += f"🚃\n{formatted}\n"
            message += f"{item['url']}\n\n"
        send_line_message(message.strip())
    else:
        print("📭 新着なし〜")

    save_current(current)

if __name__ == "__main__":
    main()
