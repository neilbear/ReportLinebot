from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    ImageMessage  # 新增圖片訊息支援
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
import json
import os

app = Flask(__name__)

# 重要：建議將憑證儲存在環境變數中
configuration = Configuration(
    access_token='tenvf9n2QkkW2O5KORk24yuK/JG6z2TRunPRVrc8rIna1ZpImWXuBAkwnV2iLqjPjH04TP2Pb2rYiA9vdr1lG6dVL6Fld6L0UPHQDYBm213nP1DrN1ZAX4VNf9lfR7vT1mdDqvHCuBBMBSMBgwWXHAdB04t89/1O/w1cDnyilFU='
)
handler = WebhookHandler('7674bdd50a627908e4c0b947246229a6')

@app.route("/callback", methods=['POST'])
def callback():
    # 取得 X-Line-Signature 標頭值
    signature = request.headers['X-Line-Signature']

    # 取得請求內容
    body = request.get_data(as_text=True)
    app.logger.info("收到請求內容: " + body)

    # 處理 webhook 請求
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("簽名驗證失敗，請檢查您的頻道存取權杖/頻道密鑰")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # 取得使用者傳送的訊息
    user_message = event.message.text
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        if user_message == '近期優惠':
            # 回傳圖片訊息
            img_url = 'https://upload.wikimedia.org/wikipedia/en/a/a6/Pok%C3%A9mon_Pikachu_art.png'
            messages = [
                ImageMessage(
                    original_content_url=img_url,
                    preview_image_url=img_url
                )
            ]
        else:
            # 預設回傳相同文字
            messages = [TextMessage(text=f"{user_message}")]
        
        # 回覆訊息
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages
            )
        )

# 串接資料庫

def init_db():
    conn = sqlite3.connect('你的db檔名')
    print ("資料庫打開成功")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            column_one TEXT NOT NULL,
            column_two TEXT NOT NULL
        )
    ''')
    print ("資料庫創建成功")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    app.run()