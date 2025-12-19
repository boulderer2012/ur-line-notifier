import os
import json
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# LINE設定
CHANNEL_ACCESS_TOKEN = 'me2oYNhNaPds9QcrFaz9r9dQXpl3ES7cDVJ+fi0N4aCbguag0tKl4W9BKEMOoLY9dhSuY239HMD+RkyhA8rlX7t3nIld6JH1s5UJHDIGu51TDAPh5EQ2p66q9FERS3iziROPKUJwNp/4djpYTsWgPwdB04t89/1O/w1cDnyilFU='
USER_ID = 'U70bcd6fc61098e0b980e9292e6083bcd'

def send_line_message(message):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    body = {
        'to': USER_ID,
        'messages': [{'type': 'text', 'text': message}]
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    print(f'📤 ステータスコード: {response.status_code}')
    print(f'📨 レスポンス: {response.text}')

def fetch_ur_listings():
    chrome_driver_path = "C:\\Temp\\UR賃貸スクレイピング\\chromedriver.exe"
    url = "https://www.ur-net.go.jp/chintai/information/"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--blink-settings=imagesEnabled=false")
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)
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
    return listings

def load_previous():
    if os.path.exists("previous.json"):
        with open("previous.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_current(data):
    with open("previous.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def detect_new_listings(current, previous):
    previous_titles = {item["title"] for item in previous}
    return [item for item in current if item["title"] not in previous_titles]

def main():
    current = fetch_ur_listings()
    previous = load_previous()
    new_list = detect_new_listings(current, previous)

    if new_list:
        print(f"🔔 {len(new_list)} 件の新着物件を検出！")
        for item in new_list:
            message = f"🏠 新着物件！\n{item['title']}\n{item['url']}"
            send_line_message(message)
        save_current(current)
    else:
        print("📭 新着なし〜")

if __name__ == "__main__":
    main()
