import os
import openai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# LINEとOpenAIの設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
openai.api_key = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # OpenAIに問い合わせ
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # または gpt-4
            messages=[
                {"role": "system", "content": "あなたは親しみやすく丁寧なアシスタントです。"},
                {"role": "user", "content": user_message}
            ]
        )
        reply_text = response.choices[0].message.content.strip()
    except Exception as e:
        reply_text = f"エラーが発生しました: {e}"

    # LINEに返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(port=5000)
