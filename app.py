from flask import Flask, request, abort, jsonify, make_response
from flask import send_from_directory

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

import sqlite3
import random

app = Flask(__name__)

configuration = Configuration(access_token='tenvf9n2QkkW2O5KORk24yuK/JG6z2TRunPRVrc8rIna1ZpImWXuBAkwnV2iLqjPjH04TP2Pb2rYiA9vdr1lG6dVL6Fld6L0UPHQDYBm213nP1DrN1ZAX4VNf9lfR7vT1mdDqvHCuBBMBSMBgwWXHAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('7674bdd50a627908e4c0b947246229a6')

# 優惠資料
promotions = [
    {
        "title": "🍔 漢堡套餐優惠",
        "description": "任選漢堡 + 薯條 + 飲料",
        "price": "套餐優惠減$30",
        "period": "長期優惠",
        "discount_amount": 30,
        "condition": "combo_burger"
    },
    {
        "title": "🥤 飲料買一送一",
        "description": "所有飲品買一杯送一杯",
        "price": "第二杯免費",
        "period": "長期優惠",
        "discount_amount": 0,
        "condition": "drink_bogo"
    },
    {
        "title": "🍟 薯條升級優惠",
        "description": "點任何主餐時薯條免費升級",
        "price": "升級優惠減$10",
        "period": "長期優惠",
        "discount_amount": 10,
        "condition": "fries_upgrade"
    },
    {
        "title": "🥘 蛋餅特價",
        "description": "所有蛋餅類商品特價",
        "price": "每份減$5",
        "period": "長期優惠",
        "discount_amount": 5,
        "condition": "omelet_discount"
    }
]

# 計算優惠折扣
# 計算優惠折扣
def calculate_discount(items):
    total_discount = 0
    item_names = [item['name'] for item in items]
    
    # 1. 漢堡套餐優惠：漢堡+薯條+飲料減$30
    has_burger = any('漢堡' in name for name in item_names)
    has_fries = '薯條' in item_names
    has_drink = any(name in ['紅茶', '豆漿', '奶茶', '綠茶'] for name in item_names)  # 新增綠茶
    
    if has_burger and has_fries and has_drink:
        total_discount += 30
    
    # 2. 蛋餅特價：每份蛋餅減$5
    omelet_count = sum(item['quantity'] for item in items if '蛋餅' in item['name'])
    total_discount += omelet_count * 5
    
    # 3. 薯條升級優惠：有主餐時薯條減$10
    has_main_dish = any(name in ['漢堡', '起司豬排漢堡', '鐵板麵', '鍋燒意麵'] for name in item_names)  # 新增主餐類別
    if has_main_dish and has_fries:
        total_discount += 10
    
    return total_discount

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

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
    original_total = data.get('total_amount', 0)
    
    # 計算優惠折扣
    discount = calculate_discount(items)
    final_total = max(0, original_total - discount)

    conn = sqlite3.connect('order.db')
    c = conn.cursor()

    names = ", ".join([item['name'] for item in items])
    quantities = ", ".join([str(item['quantity']) for item in items])
    prices = ", ".join([str(item['price']) for item in items])
    status = random.choice(['製作中', '已完成'])
    
    c.execute('INSERT INTO orders (user_id, column_one, column_two, prices, original_total, discount, final_total, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
              (user_id, names, quantities, prices, original_total, discount, final_total, status))

    conn.commit()
    order_id = c.lastrowid
    conn.close()

    return jsonify({
        'order_id': order_id,
        'original_total': original_total,
        'discount': discount,
        'final_total': final_total
    })

def init_db():
    conn = sqlite3.connect('order.db')
    print("資料庫打開成功")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            column_one TEXT NOT NULL,
            column_two TEXT NOT NULL,
            prices TEXT,
            original_total INTEGER DEFAULT 0,
            discount INTEGER DEFAULT 0,
            final_total INTEGER DEFAULT 0,
            status TEXT NOT NULL
        )
    ''')
    print("資料庫創建成功")
    conn.commit()
    conn.close()

@app.route('/order', methods=['GET'])
def order_page():
    return send_from_directory('html', 'order.html')

@app.route('/information', methods=['GET'])
def information_page():
    return send_from_directory('html', 'information.html')

@app.route('/html/<path:filename>')
def serve_html(filename):
    return send_from_directory('html', filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

user_query_status = {}

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_message = event.message.text.strip()
        user_id = event.source.user_id

        if user_query_status.get(user_id, False):
            # 用戶正在輸入訂單ID
            try:
                order_id = int(user_message)
                conn = sqlite3.connect('order.db')
                cursor = conn.cursor()
                cursor.execute("SELECT status, column_one, column_two, original_total, discount, final_total FROM orders WHERE id = ?", (order_id,))
                result = cursor.fetchone()
                conn.close()

                if result:
                    status, items, quantities, original_total, discount, final_total = result
                    item_list = items.split(", ")
                    quantity_list = quantities.split(", ")
                    
                    order_details = "\n".join([f"• {item}: {qty}份" for item, qty in zip(item_list, quantity_list)])
                    
                    reply_text = f"📋 訂單編號：{order_id}\n" + \
                                f"📊 訂單狀態：{status}\n" + \
                                f"🍽️ 訂購內容：\n{order_details}\n" + \
                                f"💰 原價：${original_total}\n"
                    
                    if discount > 0:
                        reply_text += f"🎉 優惠折扣：-${discount}\n"
                    
                    reply_text += f"💳 應付金額：${final_total}\n" + \
                                 f"🏪 請至櫃台結帳"
                else:
                    reply_text = "未找到該訂單，請檢查訂單號碼是否正確。"
            except ValueError:
                reply_text = "訂單號無效，請輸入有效的訂單ID。"
            
            # 重置查詢狀態
            user_query_status[user_id] = False
            
        else:
            # 處理一般指令
            if user_message.lower() == "訂單查詢":
                reply_text = "請輸入訂單ID以查詢訂單狀態。"
                user_query_status[user_id] = True
            elif user_message.lower() in ["近期優惠", "優惠", "促銷", "特價"]:
                reply_text = "🎉 近期優惠活動 🎉\n\n"
                for i, promo in enumerate(promotions, 1):
                    reply_text += f"{i}. {promo['title']}\n"
                    reply_text += f"   {promo['description']}\n"
                    reply_text += f"   💰 {promo['price']}\n"
                    reply_text += f"   📅 {promo['period']}\n\n"
                reply_text += "📞 歡迎來店享用或線上訂購！"
            else:
                reply_text = "請輸入以下指令：\n• '訂單查詢' - 查詢訂單狀態\n• '近期優惠' - 查看最新優惠活動"

        # 發送回覆訊息
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

# 添加中間件處理ngrok header
# 刪除整個 handle_ngrok_warning 函數
# @app.before_request
# def handle_ngrok_warning():
#     if 'ngrok-skip-browser-warning' in request.headers:
#         app.logger.info("Request with ngrok-skip-browser-warning header received")

@app.after_request
def after_request(response):
    # 添加CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == "__main__":
    init_db()
    app.run(port=5001)