from flask import Flask, request, abort, jsonify, send_from_directory

# 添加Firebase导入
import firebase_admin
from firebase_admin import credentials, firestore

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# 删除SQLite导入
# import sqlite3
import random

app = Flask(__name__)

# Firebase初始化
cred = credentials.Certificate('linebot-1e553-firebase-adminsdk-fbsvc-660359af2b.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

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

@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'GET':
        return send_from_directory('html', 'order.html')
    elif request.method == 'POST':
        # 處理訂單提交
        data = request.get_json()
        user_id = data.get('user_id', 'guest')
        items = data.get('items')
        original_total = data.get('total_amount', 0)
        
        # 計算優惠折扣
        discount = calculate_discount(items)
        final_total = max(0, original_total - discount)
    
        names = ", ".join([item['name'] for item in items])
        quantities = ", ".join([str(item['quantity']) for item in items])
        prices = ", ".join([str(item['price']) for item in items])
        status = random.choice(['製作中', '已完成'])
        
        # 生成數字訂單編號
        try:
            # 查詢現有訂單數量來生成下一個編號
            all_orders = list(db.collection('orders').stream())
            next_order_number = len(all_orders) + 1
            
            # 建立訂單資料
            order_data = {
                'order_number': next_order_number,  # 數字訂單編號
                'user_id': user_id,
                'items': names,
                'quantities': quantities,
                'prices': prices,
                'original_total': original_total,
                'discount': discount,
                'final_total': final_total,
                'status': status,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            
            # 使用數字編號作為文檔ID
            db.collection('orders').document(str(next_order_number)).set(order_data)
            
            return jsonify({
                'success': True, 
                'message': '訂單已成功提交！',
                'order_id': next_order_number,  # 返回數字訂單編號
                'final_total': final_total,
                'discount': discount
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_message = event.message.text.strip()
        user_id = event.source.user_id

        # 在handle_message函數中修改訂單查詢部分
        if user_query_status.get(user_id, False):
            try:
                order_id = user_message.strip()
                
                # 從Realtime Database查詢訂單
                order_ref = ref.child('orders').child(order_id)
                order_data = order_ref.get()
                
                if order_data:
                    status = order_data.get('status')
                    items = order_data.get('items')
                    quantities = order_data.get('quantities')
                    original_total = order_data.get('original_total')
                    discount = order_data.get('discount')
                    final_total = order_data.get('final_total')
                    
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
            except Exception as e:
                reply_text = f"查詢訂單時發生錯誤，請稍後再試。"
            
            # 重置查询状态
            user_query_status[user_id] = False
            
        else:
            # 处理一般指令
            if user_message.lower() == "订单查询":
                reply_text = "请输入订单ID以查询订单状态。"
                user_query_status[user_id] = True
            elif user_message.lower() in ["近期优惠", "优惠", "促销", "特价"]:
                reply_text = "🎉 近期优惠活动 🎉\n\n"
                for i, promo in enumerate(promotions, 1):
                    reply_text += f"{i}. {promo['title']}\n"
                    reply_text += f"   {promo['description']}\n"
                    reply_text += f"   💰 {promo['price']}\n"
                    reply_text += f"   📅 {promo['period']}\n\n"
                reply_text += "📞 欢迎来店享用或线上订购！"
            elif '查詢訂單' in user_message:
                try:
                    # 從 Firestore 查詢訂單
                    orders_ref = db.collection('orders')
                    query = orders_ref.where('user_id', '==', user_id).limit(5)
                    orders = query.stream()
                    
                    order_list = []
                    for order in orders:
                        order_data = order.to_dict()
                        # 使用數字訂單編號
                        order_number = order_data.get('order_number', order.id)
                        order_list.append(f"訂單編號: {order_number}\n商品: {order_data.get('items', 'N/A')}\n狀態: {order_data.get('status', 'N/A')}\n總金額: ${order_data.get('final_total', 0)}")
                    
                    if order_list:
                        reply_text = "您的最近訂單：\n\n" + "\n\n".join(order_list)
                    else:
                        reply_text = "目前沒有找到您的訂單記錄。"
                        
                except Exception as e:
                    reply_text = f"查詢訂單時發生錯誤: {str(e)}"
            # 處理訂單編號查詢
            elif user_message.strip().isdigit():  # 檢查是否為數字
                order_number = user_message.strip()
                
                try:
                    # 從 Firestore 查詢特定訂單（使用數字編號作為文檔ID）
                    order_ref = db.collection('orders').document(order_number)
                    order_doc = order_ref.get()
                    
                    if order_doc.exists:
                        order_data = order_doc.to_dict()
                        status = order_data.get('status')
                        items = order_data.get('items')
                        quantities = order_data.get('quantities')
                        original_total = order_data.get('original_total')
                        discount = order_data.get('discount')
                        final_total = order_data.get('final_total')
                        
                        item_list = items.split(", ")
                        quantity_list = quantities.split(", ")
                        
                        order_details = "\n".join([f"• {item}: {qty}份" for item, qty in zip(item_list, quantity_list)])
                        
                        reply_text = f"📋 訂單編號：{order_number}\n" + \
                                       f"📦 訂單內容：\n{order_details}\n" + \
                                       f"💰 原價：${original_total}\n" + \
                                       f"🎁 優惠折扣：${discount}\n" + \
                                       f"💳 實付金額：${final_total}\n" + \
                                       f"📊 訂單狀態：{status}"
                    else:
                        reply_text = f"找不到訂單編號 {order_number} 的相關資料。"
                        
                except Exception as e:
                    reply_text = f"查詢訂單時發生錯誤: {str(e)}"
            else:
                reply_text = "请输入以下指令：\n• '订单查询' - 查询订单状态\n• '近期优惠' - 查看最新优惠活动\n• 或直接輸入數字訂單編號查詢特定訂單"

        # 发送回复消息
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 7860))  # Hugging Face Spaces 預設使用 7860 port
    app.run(host='0.0.0.0', port=port)
