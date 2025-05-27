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

app = Flask(__name__, static_folder='static')

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
    items = data.get('items', [])
    conn = sqlite3.connect('order.db')
    c = conn.cursor()
    # 建立訂單主表
    c.execute('INSERT INTO orders (user_id) VALUES (?)', (user_id,))
    order_id = c.lastrowid
    # 建立訂單明細表
    for item in items:
        c.execute('INSERT INTO order_items (order_id, item, quantity) VALUES (?, ?, ?)', (order_id, item['item'], item['quantity']))
    conn.commit()
    conn.close()
    return jsonify({'order_id': order_id})

# Initialize database
def init_db():
    conn = sqlite3.connect('order.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/order', methods=['GET'])
def order_page():
    return send_from_directory('html', 'order.html')



@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

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
    init_db()
    app.run(port=5001)