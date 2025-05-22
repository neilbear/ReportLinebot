from flask import Flask, request, abort ,jsonify

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
 # 接收訂單
@app.route("/order", methods=["POST"])
def order():
    # 获取订单数据
    order_data = request.json
    
    # 连接到数据库
    conn = sqlite3.connect('order.db')
    cursor = conn.cursor()
    
    # 插入订单数据
    cursor.execute("INSERT INTO orders (user_id, column_one, column_two) VALUES (?, ?, ?)", (order_data['user_id'], order_data['column_one'], order_data['column_two']))
    conn.commit()
    
    # 获取生成的订单ID
    order_id = cursor.lastrowid
    conn.close()
    
    # 返回确认消息
    return jsonify({"message": "訂單已接收", "order_id": order_id})

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
            column_two TEXT NOT NULL
        )
    ''')
    print ("資料庫創建成功")
    conn.commit()
    conn.close()


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        conn = sqlite3.connect('order.db')
        cursor = conn.cursor()
        
        # 查询订单状态
        order_id = event.message.text  # 假设用户发送订单号
        cursor.execute("SELECT status FROM orders WHERE order_id = ?", (order_id,))
        result = cursor.fetchone()
        
        # 检查查询结果并回复
        if result:
            status = result[0]
            reply_text = f"您的訂單狀態是：{status}"
        else:
            reply_text = "未找到該訂單，請檢查訂單號碼是否正確。"
        
        # 关闭数据库连接
        conn.close()
        
        # 回复用户
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    app.run(port=5001)