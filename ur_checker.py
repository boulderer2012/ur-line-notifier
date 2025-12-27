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
    options.add_argument("--headless")  # 画面を表示しない
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

# 🔹 コンフォール東朝霞のリノベ済み物件を抽出
def fetch_renovated_higashi_asaka():
    url = "https://www.ur-net.go.jp/chintai/kanto/saitama/result/?line_station=14400_1488&todofuken=saitama"
    driver = create_driver()
    driver.get(url)
    time.sleep(5)  # JavaScriptでの読み込み待ち

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    listings = []
    base_url = "https://www.ur-net.go.jp"
    cards = soup.select("div.section_inner > ul > li")  # 物件カード一覧

    for card in cards:
        name_tag = card.select_one("p.property_name")
        if not name_tag or "コンフォール東朝霞" not in name_tag.text:
            continue  # 他の物件はスキップ

        detail_link = card.select_one("a")
        if not detail_link:
            continue

        url = base_url + detail_link.get("href")
        title = name_tag.text.strip()

        # 各情報を抽出
        layout = card.select_one("p.layout")
        size = card.select_one("p.size")
        floor = card.select_one("p.floor")
        remarks = card.select_one("p.comment")

        layout_text = layout.text.strip() if layout else ""
        size_text = size.text.strip() if size else ""
        floor_text = floor.text.strip() if floor else ""
        remarks_text = remarks.text.strip() if remarks else ""

        # 条件に合致するかチェック
        if not is_layout_ok(layout_text):
            continue
        if not is_size_ok(size_text):
            continue
        if not is_floor_ok(floor_text):
            continue
        if "リノベーション" not in remarks_text:
            continue

        # 条件を満たす物件を追加
        listings.append({
            "title": f"{title} {layout_text} {size_text} {floor_text}",
            "url": url
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

    # 🔍 東朝霞リノベ物件も追加でチェック！
    listings += fetch_renovated_higashi_asaka()

    return listings

# 🔹 前回との差分を検出（title + url のペアで比較）
def detect_new_listings(current, previous):
    previous_set = {(item["title"], item["url"]) for item in previous}
    return [item for item in current if (item["title"], item["url"]) not in previous_set]

# 🔹 メイン処理
def main():
    # 現在時刻（JST）を取得
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    print(f"🕒 チェック実行時刻（JST）: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    current = fetch_ur_listings()
    previous = load_previous()

    # 初回実行や previous.json が空のときは通知せず保存だけ
    if not previous:
        print("📂 初回実行または previous.json が空のため、通知せず保存のみ行います。")
        save_current(current)
        return

    # 差分を検出
    new_list = detect_new_listings(current, previous)
    MAX_ITEMS = 5  # 通知する最大件数

    if new_list:
        print(f"🔔 {len(new_list)} 件の新着物件を検出！")
        message = f"🏠 新着物件一覧（{now.strftime('%Y/%m/%d %H:%M')} 時点）\n\n"
        for item in new_list[:MAX_ITEMS]:
            message += f"{item['title']}\n{item['url']}\n\n"
        send_line_message(message.strip())
    else:
        print("📭 新着なし〜")

    # 最新の物件リストを保存
    save_current(current)

# 🔹 スクリプトのエントリーポイント
if __name__ == "__main__":
    main()
