from flask import Flask, request, abort ,jsonify
from flask import send_from_directory

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

import sqlite3
import random

app = Flask(__name__)

configuration = Configuration(access_token='tenvf9n2QkkW2O5KORk24yuK/JG6z2TRunPRVrc8rIna1ZpImWXuBAkwnV2iLqjPjH04TP2Pb2rYiA9vdr1lG6dVL6Fld6L0UPHQDYBm213nP1DrN1ZAX4VNf9lfR7vT1mdDqvHCuBBMBSMBgwWXHAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('7674bdd50a627908e4c0b947246229a6')


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'
@app.route('/order', methods=['POST'])
def order():
    data = request.get_json()
    user_id = data.get('user_id', 'guest')
    items = data.get('items')

    conn = sqlite3.connect('order.db')
    c = conn.cursor()

    names = ", ".join([item['name'] for item in items])
    quantities = ", ".join([str(item['quantity']) for item in items])
    # 随机选择状态
    status = random.choice(['製作中', '已完成'])
    c.execute('INSERT INTO orders (user_id, column_one, column_two, status) VALUES (?, ?, ?, ?)', (user_id, names, quantities, status))

    conn.commit()
    order_id = c.lastrowid
    conn.close()

    return jsonify({'order_id': order_id})

# Initialize database
def init_db():
    conn = sqlite3.connect('order.db')
    print ("資料庫打開成功")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            column_one TEXT NOT NULL,
            column_two TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    print ("資料庫創建成功")
    conn.commit()
    conn.close()


@app.route('/order', methods=['GET'])
def order_page():
    return send_from_directory('html', 'order.html')
from flask import send_from_directory

@app.route('/html/<path:filename>')
def serve_html(filename):
    return send_from_directory('html', filename)

# 全局字典用于存储用户的查询状态
user_query_status = {}

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_message = event.message.text.strip()
        user_id = event.source.user_id

        # 检查用户的查询状态
        if user_query_status.get(user_id, False):
            try:
                order_id = int(user_message)
                conn = sqlite3.connect('order.db')
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
                result = cursor.fetchone()
                conn.close()

                if result:
                    status = result[0]
                    reply_text = f"您的訂單狀態是：{status}"
                else:
                    reply_text = "未找到該訂單，請檢查訂單號碼是否正確。"
            except ValueError:
                reply_text = "訂單號無效，請輸入有效的訂單ID。"

            # 重置用户的查询状态
            user_query_status[user_id] = False
        else:
            # 检查用户是否请求查询订单
            if user_message.lower() == "訂單查詢":
                reply_text = "請輸入訂單ID以查詢訂單狀態。"
                # 设置用户的查询状态
                user_query_status[user_id] = True
            else:
                reply_text = "請先輸入‘訂單查詢’以開始查詢訂單狀態。"

        # 回复用户
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    init_db()
    app.run(port=5001)