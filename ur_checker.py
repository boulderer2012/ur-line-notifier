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

# 🔸 環境変数の読み込み
load_dotenv()

# 🔸 差分保存用のファイルパス
DATA_PATH = "previous.json"

# 🔹 前回の物件リストを読み込む
def load_previous(): 
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# 🔹 今回取得した物件リストを保存
def save_current(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 🔸 LINE通知設定（環境変数から取得）
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
GROUP_ID = os.environ.get("LINE_GROUP_ID")

# 🔹 LINEグループにメッセージを送信
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

# 🔹 Selenium用のChromeドライバを作成
def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

# 🔹 間取りが2DK以上かを判定
def is_layout_ok(layout):
    match = re.match(r"(\d+)[DLK]+", layout)
    if match:
        return int(match.group(1)) >= 2
    return False

# 🔹 面積が60㎡以上かを判定
def is_size_ok(size_str):
    try:
        return float(size_str.replace("㎡", "").strip()) >= 60.0
    except:
        return False

# 🔹 階数が3階以上かを判定
def is_floor_ok(floor_str):
    match = re.search(r"(\d+)階", floor_str)
    if match:
        return int(match.group(1)) >= 3
    return False

# 🔹 コンフォール東朝霞のリノベ済み物件を抽出（本番用）
def fetch_renovated_higashi_asaka():
    url = "https://www.ur-net.go.jp/chintai/kanto/saitama/result/?line_station=14400_1488&todofuken=saitama"
    driver = create_driver()
    driver.get(url)
    
    # 物件カードが読み込まれるまで待機
    wait = WebDriverWait(driver, 20)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.section_inner ul li")))
    except:
        print("⚠️ 物件カードの読み込みタイムアウト")
        driver.quit()
        return []

    time.sleep(3)  # 念のため追加待機

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    listings = []
    base_url = "https://www.ur-net.go.jp"
    cards = soup.select("div.section_inner > ul > li")
    
    print(f"🔍 取得したカード数: {len(cards)}")  # デバッグ用

    for card in cards:
        name_tag = card.select_one("p.property_name")
        if not name_tag or "コンフォール東朝霞" not in name_tag.text:
            continue

        detail_link = card.select_one("a")
        if not detail_link:
            continue

        href = detail_link.get("href")
        full_url = base_url + href
        title = name_tag.text.strip()

        layout = card.select_one("p.layout")
        size = card.select_one("p.size")
        floor = card.select_one("p.floor")

        layout_text = layout.text.strip() if layout else ""
        size_text = size.text.strip() if size else ""
        floor_text = floor.text.strip() if floor else ""

        print(f"🏠 発見: {title} {layout_text} {size_text} {floor_text}")  # デバッグ用

        if not (is_layout_ok(layout_text) and is_size_ok(size_text) and is_floor_ok(floor_text)):
            continue

        listings.append({
            "title": f"{title} {layout_text} {size_text} {floor_text}",
            "url": full_url
        })

    return listings
    
# 🔹 UR公式お知らせページから新築物件を取得＋東朝霞リノベ物件も追加
def fetch_ur_listings():
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
            listings.append({"title": text, "url": base_url + href})

    # 東朝霞リノベ物件も追加
    listings += fetch_renovated_higashi_asaka()

    return listings

# 🔹 前回との差分を検出
def detect_new_listings(current, previous):
    previous_set = {(item["title"], item["url"]) for item in previous}
    return [item for item in current if (item["title"], item["url"]) not in previous_set]

# 🔹 メイン処理
def main():
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    print(f"🕒 チェック実行時刻（JST）: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    current = fetch_ur_listings()
    previous = load_previous()

    if not previous:
        print("📂 初回実行または previous.json が空のため、通知せず保存のみ行います。")
        save_current(current)
        return

    new_list = detect_new_listings(current, previous)
    MAX_ITEMS = 5

    if new_list:
        print(f"🔔 {len(new_list)} 件の新着物件を検出！")
        message = f"🏠 新着物件一覧（{now.strftime('%Y/%m/%d %H:%M')} 時点）\n\n"
        for item in new_list[:MAX_ITEMS]:
            message += f"{item['title']}\n{item['url']}\n\n"
        send_line_message(message.strip())
    else:
        print("📭 新着なし〜")

    save_current(current)

# 🔹 エントリーポイント
if __name__ == "__main__":
    main()
