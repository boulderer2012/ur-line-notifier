from flask import Flask, request, abort
import json

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data(as_text=True)
    print("📩 Webhook受信！")
    print(body)
    return "OK", 200

if __name__ == "__main__":
    app.run(port=8000)
