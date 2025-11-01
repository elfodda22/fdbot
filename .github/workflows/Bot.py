import json
import telebot
from flask import Flask, request
import threading
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import os
from urllib.parse import urlparse, parse_qs
import urllib.parse
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Initialize the bot with the token
TELEGRAM_TOKEN_BOT = os.getenv('TELEGRAM_BOT_TOKEN')
ALIEXPRESS_API_PUBLIC = os.getenv('ALIEXPRESS_API_PUBLIC')
ALIEXPRESS_API_SECRET = os.getenv('ALIEXPRESS_API_SECRET')

# Check if required environment variables are set
if not TELEGRAM_TOKEN_BOT:
    print("❌ Error: TELEGRAM_BOT_TOKEN environment variable is not set!")
    print("Please set the environment variable or create a .env file with your bot token.")
    exit(1)

if not ALIEXPRESS_API_PUBLIC or not ALIEXPRESS_API_SECRET:
    print("❌ Error: ALIEXPRESS_API_PUBLIC and ALIEXPRESS_API_SECRET environment variables are not set!")
    print("Please set the environment variables or create a .env file with your API credentials.")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN_BOT)

# Initialize Aliexpress API
try:
    aliexpress = AliexpressApi(ALIEXPRESS_API_PUBLIC, ALIEXPRESS_API_SECRET,
                               models.Language.AR, models.Currency.EUR, 'telegrameBot')
    print("✅ AliExpress API initialized successfully.")
except Exception as e:
    print(f"❌ Error initializing AliExpress API: {e}")

# Define keyboards
keyboardStart = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ صفحة مراجعة وجمع النقاط يوميا ⭐️", url="https://s.click.aliexpress.com/e/_c42am68R")
btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click')
btn3 = types.InlineKeyboardButton("❤️ اشترك في القناة للمزيد من العروض ❤️", url="https://t.me/AliExPressuperDeals")
btn4 = types.InlineKeyboardButton("🎬 شاهد كيفية عمل البوت 🎬", url="https://t.me/ShopAliExpressMaroc/9")
btn5 = types.InlineKeyboardButton("💰 حمل تطبيق Aliexpress عبر الضغط هنا للحصول على مكافأة 5 دولار 💰", url="https://a.aliexpress.com/_mtV0j3q")
keyboardStart.add(btn1, btn2, btn3, btn4)

keyboard = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ صفحة مراجعة وجمع النقاط يوميا ⭐️", url="https://s.click.aliexpress.com/e/_c42am68R")
btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click')
btn3 = types.InlineKeyboardButton("❤️ اشترك في القناة للمزيد من العروض ❤️", url="https://t.me/AliExPressuperDeals")
keyboard.add(btn1, btn2, btn3)

keyboard_games = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ صفحة مراجعة وجمع النقاط يوميا ⭐️", url="https://s.click.aliexpress.com/e/_c42am68R")
btn2 = types.InlineKeyboardButton("⭐️ لعبة Merge boss ⭐️", url="https://s.click.aliexpress.com/e/_DlCyg5Z")
btn3 = types.InlineKeyboardButton("⭐️ لعبة Fantastic Farm ⭐️", url="https://s.click.aliexpress.com/e/_DBBkt9V")
btn4 = types.InlineKeyboardButton("⭐️ لعبة قلب الاوراق Flip ⭐️", url="https://s.click.aliexpress.com/e/_DdcXZ2r")
btn5 = types.InlineKeyboardButton("⭐️ لعبة GoGo Match ⭐️", url="https://s.click.aliexpress.com/e/_DDs7W5D")
keyboard_games.add(btn1, btn2, btn3, btn4, btn5)

# User tracking functions
def track_user(user_id, username=None, first_name=None):
    """Track unique users in a JSON file"""
    try:
        # Load existing users
        try:
            with open('users.json', 'r', encoding='utf-8') as f:
                users = json.load(f)
        except FileNotFoundError:
            users = {}
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add new user if not exists
        if str(user_id) not in users:
            users[str(user_id)] = {
                'username': username,
                'first_name': first_name,
                'first_seen': current_time,
                'last_seen': current_time,
                'message_count': 1
            }
            print(f"✅ New user added: {user_id} (@{username})")
        else:
            # Update existing user
            users[str(user_id)]['last_seen'] = current_time
            users[str(user_id)]['message_count'] += 1
            # Update username/first_name if changed
            if username:
                users[str(user_id)]['username'] = username
            if first_name:
                users[str(user_id)]['first_name'] = first_name
        
        # Save updated users
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        
        return len(users)
    except Exception as e:
        print(f"❌ Error tracking user: {e}")
        return 0

def get_user_stats():
    """Get statistics about bot users"""
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        total_users = len(users)
        total_messages = sum(user['message_count'] for user in users.values())
        
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Count users who joined today
        new_today = sum(1 for user in users.values() 
                       if user['first_seen'].startswith(today))
        
        # Count active users today
        active_today = sum(1 for user in users.values() 
                          if user['last_seen'].startswith(today))
        
        return {
            'total_users': total_users,
            'total_messages': total_messages,
            'new_today': new_today,
            'active_today': active_today
        }
    except FileNotFoundError:
        return {
            'total_users': 0,
            'total_messages': 0,
            'new_today': 0,
            'active_today': 0
        }
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return None

# Define function to get exchange rates from USD to MAD and DZD
def get_exchange_rates():
    """Fetch current exchange rates for MAD and DZD"""
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
        data = response.json()
        return {
            'MAD': data['rates']['MAD'],
            'DZD': data['rates']['DZD']
        }
    except Exception as e:
        print(f"❌ Error fetching exchange rates: {e}")
        return None

# Define function to resolve redirect chain and get final URL
def resolve_full_redirect_chain(link):
    """Resolve all redirects to get the final URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.36'
    }
    try:
        session_req = requests.Session()
        response = session_req.get(link, allow_redirects=True, timeout=10, headers=headers)
        final_url = response.url
        print(f"🔗 Resolved URL: {link} -> {final_url}")
        
        if "star.aliexpress.com" in final_url:
            # Extract redirectUrl parameter
            parsed_url = urlparse(final_url)
            params = parse_qs(parsed_url.query)
            if 'redirectUrl' in params:
                redirect_url = params['redirectUrl'][0]
                print(f"🔗 Found redirectUrl: {redirect_url}")
                return redirect_url
        
        if "aliexpress.com/item" in final_url:
            return final_url
        elif "p/coin-index" in final_url:
            return final_url
        else:
            return final_url
    except requests.RequestException as e:
        print(f"❌ Error resolving redirect chain for link {link}: {e}")
        return link  # Return original link if resolution fails

# Define function to extract product ID from link
def extract_product_id(link):
    """Extract product ID from AliExpress link (handles redirected/shortened links)"""
    print(f"🔍 Extracting product ID from: {link}")
    
    # First resolve any redirects to get the final URL
    resolved_link = resolve_full_redirect_chain(link)
    print(f"🔗 Using resolved link: {resolved_link}")
    
    # Standard product page pattern
    product_id_pattern = r'/item/(\d+)\.html'
    match = re.search(product_id_pattern, resolved_link)
    if match:
        print(f"✅ Extracted product ID (standard): {match.group(1)}")
        return match.group(1)
    
    # Coin page pattern - extract from productIds parameter
    coin_page_pattern = r'productIds=(\d+)'
    coin_match = re.search(coin_page_pattern, resolved_link)
    if coin_match:
        print(f"✅ Extracted product ID (coin-index): {coin_match.group(1)}")
        return coin_match.group(1)
    
    # Alternative pattern for different URL formats (long product IDs)
    product_id_pattern_alt = r'(\d{13,})'  # Long product IDs
    match_alt = re.search(product_id_pattern_alt, resolved_link)
    if match_alt:
        print(f"✅ Extracted product ID (long format): {match_alt.group(1)}")
        return match_alt.group(1)
    
    print(f"❌ Could not extract product ID from: {resolved_link}")
    return None

# Define function to generate coin-index affiliate link for 620 channel
def generate_coin_affiliate_link(product_id):
    """Generate affiliate link using coin-index system for 620 channel"""
    try:
        # Create the coin-index URL
        coin_index_url = f"https://m.aliexpress.com/p/coin-index/index.html?_immersiveMode=true&from=syicon&productIds={product_id}"
        
        # Generate affiliate link using the coin-index URL
        affiliate_link = aliexpress.get_affiliate_links(coin_index_url)
        return affiliate_link[0].promotion_link
    except Exception as e:
        print(f"❌ Error generating coin affiliate link for product {product_id}: {e}")
        return None

# Define function to generate bundle affiliate link for 560 channel
def generate_bundle_affiliate_link(product_id, original_link):
    """Generate affiliate link using bundle system for 560 channel"""
    try:
        # Create the bundle URL with sourceType=560
        bundle_url = f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={original_link}?sourceType=560&aff_fcid='
        
        # Generate affiliate link using the bundle URL
        affiliate_link = aliexpress.get_affiliate_links(bundle_url)
        return affiliate_link[0].promotion_link
    except Exception as e:
        print(f"❌ Error generating bundle affiliate link for product {product_id}: {e}")
        return None

# Define bot handlers
@bot.message_handler(commands=['start'])
def welcome_user(message):
    print("Handling /start command")
    
    # Track the user
    total_users = track_user(
        message.from_user.id, 
        message.from_user.username,
        message.from_user.first_name
    )
    print(f"📊 Total users: {total_users}")
    
    bot.send_message(
        message.chat.id,
        "مرحبا بكم👋 \n" 
        "أنا علي إكسبريس بوت أقوم بتخفيض المنتجات و البحث  عن أفضل العروض إنسخ رابط المنتج وضعه هنا 👇 ستجد جميع عروض المنتج بثمن أقل 🔥",
        reply_markup=keyboardStart)

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """Show bot statistics - can be restricted to admin only"""
    try:
        stats = get_user_stats()
        
        if stats:
            stats_text = (
                f"📊 إحصائيات البوت:\n\n"
                f"👥 إجمالي المستخدمين: {stats['total_users']}\n"
                f"💬 إجمالي الرسائل: {stats['total_messages']}\n"
                f"🆕 مستخدمين جدد اليوم: {stats['new_today']}\n"
                f"✅ نشطين اليوم: {stats['active_today']}\n"
            )
            
            bot.send_message(message.chat.id, stats_text)
        else:
            bot.send_message(message.chat.id, "❌ حدث خطأ في جلب الإحصائيات")
    except Exception as e:
        print(f"Error in show_stats: {e}")
        bot.send_message(message.chat.id, "❌ لا توجد إحصائيات متاحة")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    try:
        print(f"Message received: {message.text}")
        
        # Track user activity
        track_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name
        )
        
        link = extract_link(message.text)
        sent_message = bot.send_message(message.chat.id, 'المرجو الانتظار قليلا، يتم تجهيز العروض ⏳')
        message_id = sent_message.message_id
        if link and "aliexpress.com" in link and not ("p/shoppingcart" in message.text.lower()):
            if "availableProductShopcartIds".lower() in message.text.lower():
                get_affiliate_shopcart_link(link, message)
                return
            get_affiliate_links(message, message_id, link)
        else:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, "الرابط غير صحيح ! تأكد من رابط المنتج أو اعد المحاولة.\n"
                                              " قم بإرسال <b> الرابط فقط</b> بدون عنوان المنتج",
                             parse_mode='HTML')
    except Exception as e:
        print(f"Error in echo_all handler: {e}")

def extract_link(text):
    link_pattern = r'https?://\S+|www\.\S+'
    links = re.findall(link_pattern, text)
    if links:
        print(f"Extracted link: {links[0]}")
        return links[0]
    return None

def get_affiliate_links(message, message_id, link):
    try:
        # Resolve the full redirect chain first
        resolved_link = resolve_full_redirect_chain(link)
        if not resolved_link:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, "❌ لم أتمكن من حل الرابط! تأكد من رابط المنتج أو أعد المحاولة.")
            return

        # Extract product ID from the resolved link
        product_id = extract_product_id(resolved_link)
        if not product_id:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, "❌ لم أتمكن من استخراج معرف المنتج من الرابط.")
            return

        # Generate coin-index affiliate link for 620 channel
        coin_affiliate_link = generate_coin_affiliate_link(product_id)
        
        # Generate bundle affiliate link for 560 channel
        bundle_affiliate_link = generate_bundle_affiliate_link(product_id, resolved_link)
        
        # Generate other affiliate links using traditional method
        super_links = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={resolved_link}?sourceType=562&aff_fcid='
        )
        super_links = super_links[0].promotion_link

        limit_links = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={resolved_link}?sourceType=561&aff_fcid='
        )
        limit_links = limit_links[0].promotion_link

        try:
            # Get product details using the product ID
            product_details = aliexpress.get_products_details([
                product_id
            ], fields=["target_sale_price", "product_title", "product_main_image_url"])
            
            if product_details and len(product_details) > 0:
                # Print all details of product in JSON format for debugging
                print(f"Product details object: {json.dumps(product_details[0].__dict__, indent=2, ensure_ascii=False)}")
                price_pro = float(product_details[0].target_sale_price)
                title_link = product_details[0].product_title
                img_link = product_details[0].product_main_image_url
                
                # Get exchange rates for both MAD and DZD
                exchange_rates = get_exchange_rates()
                if exchange_rates:
                    price_pro_mad = price_pro * exchange_rates['MAD']
                    price_pro_dzd = price_pro * exchange_rates['DZD']
                else:
                    # Fallback to USD if exchange rates not available
                    price_pro_mad = price_pro
                    price_pro_dzd = price_pro
                
                print(f"Product details: {title_link}, {price_pro}, {img_link}")
                bot.delete_message(message.chat.id, message_id)
                
                # Build the message with all affiliate links and both currencies
                message_text = (
                    f" \n🛒 منتجك هو : 🔥 \n"
                    f" {title_link} �️ \n"
                    f" سعر المنتج : "
                    f" {price_pro:.2f} دولار 💵\n"
                    f" {price_pro_mad:.2f} درهم مغربي 🇲🇦\n"
                    f" {price_pro_dzd:.2f} دينار جزائري 🇩🇿\n"
                    " \n قارن بين الاسعار واشتري 🔥 \n"
                )
                
                # Add coin-index affiliate link for 620 channel if available
                if coin_affiliate_link:
                    message_text += (
                        "💰 عرض العملات (السعر النهائي عند الدفع) : \n"
                        f"الرابط {coin_affiliate_link} \n"
                    )
                
                # Add bundle affiliate link for 560 channel if available
                if bundle_affiliate_link:
                    message_text += (
                        "📦 عرض الحزمة (عروض متنوعة) : \n"
                        f"الرابط {bundle_affiliate_link} \n"
                    )
                
                message_text += (
                    f"💎 عرض السوبر : \n"
                    f"الرابط {super_links} \n"
                    f"🔥 عرض محدود : \n"
                    f"الرابط {limit_links} \n\n"
                    "#AliExpressSaverBot ✅"
                )
                
                bot.send_photo(message.chat.id,
                               img_link,
                               caption=message_text,
                               reply_markup=keyboard)
            else:
                # Fallback if product details couldn't be fetched
                bot.delete_message(message.chat.id, message_id)
                
                # Build fallback message without product details
                message_text = "قارن بين الاسعار واشتري 🔥 \n"
                
                # Add coin-index affiliate link for 620 channel if available
                if coin_affiliate_link:
                    message_text += (
                        "💰 عرض العملات (السعر النهائي عند الدفع) : \n"
                        f"الرابط {coin_affiliate_link} \n"
                    )
                
                # Add bundle affiliate link for 560 channel if available
                if bundle_affiliate_link:
                    message_text += (
                        "📦 عرض الحزمة (عروض متنوعة) : \n"
                        f"الرابط {bundle_affiliate_link} \n"
                    )
                
                message_text += (
                    f"💎 عرض السوبر : \n"
                    f"الرابط {super_links} \n"
                    f"🔥 عرض محدود : \n"
                    f"الرابط {limit_links} \n\n"
                    "#AliExpressSaverBot ✅"
                )
                
                bot.send_message(message.chat.id, message_text, reply_markup=keyboard)
        except Exception as e:
            print(f"Error in get_affiliate_links inner try: {e}")
            bot.delete_message(message.chat.id, message_id)
            
            # Build fallback message without product details but with all affiliate links
            message_text = "قارن بين الاسعار واشتري 🔥 \n"
            
            # Add coin-index affiliate link for 620 channel if available
            if coin_affiliate_link:
                message_text += (
                    "💰 عرض العملات (السعر النهائي عند الدفع) : \n"
                    f"الرابط {coin_affiliate_link} \n"
                )
            
            # Add bundle affiliate link for 560 channel if available
            if bundle_affiliate_link:
                message_text += (
                    "📦 عرض الحزمة (عروض متنوعة) : \n"
                    f"الرابط {bundle_affiliate_link} \n"
                )
            
            message_text += (
                f"💎 عرض السوبر : \n"
                f"الرابط {super_links} \n"
                f"🔥 عرض محدود : \n"
                f"الرابط {limit_links} \n\n"
                "#AliExpressSaverBot ✅"
            )
            
            bot.send_message(message.chat.id, message_text, reply_markup=keyboard)
    except Exception as e:
        print(f"Error in get_affiliate_links: {e}")
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

def build_shopcart_link(link):
    params = get_url_params(link)
    shop_cart_link = "https://www.aliexpress.com/p/trade/confirm.html?"
    shop_cart_params = {
        "availableProductShopcartIds": ",".join(params["availableProductShopcartIds"]),
        "extraParams": json.dumps({"channelInfo": {"sourceType": "620"}}, separators=(',', ':'))
    }
    return create_query_string_url(link=shop_cart_link, params=shop_cart_params)

def get_url_params(link):
    parsed_url = urlparse(link)
    params = parse_qs(parsed_url.query)
    return params

def create_query_string_url(link, params):
    return link + urllib.parse.urlencode(params)

def get_affiliate_shopcart_link(link, message):
    try:
        shopcart_link = build_shopcart_link(link)
        affiliate_link = aliexpress.get_affiliate_links(shopcart_link)[0].promotion_link
        text2 = f"هذا رابط تخفيض السلة \n{str(affiliate_link)}"
        img_link3 = "https://i.postimg.cc/1Xrk1RJP/Copy-of-Basket-aliexpress-telegram.png"
        bot.send_photo(message.chat.id, img_link3, caption=text2)
    except Exception as e:
        print(f"Error in get_affiliate_shopcart_link: {e}")
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    try:
        print(f"Callback query received: {call.data}")
        
        # Track user activity on callback
        track_user(
            call.from_user.id,
            call.from_user.username,
            call.from_user.first_name
        )
        
        if call.data == 'click':
            # Replace with your link and message if needed
            link = 'https://www.aliexpress.com/p/shoppingcart/index.html?'
            get_affiliate_shopcart_link(link, call.message)
        else:
            bot.send_message(call.message.chat.id, "..")
            img_link2 = "https://i.postimg.cc/VvmhgQ1h/Basket-aliexpress-telegram.png"
            bot.send_photo(call.message.chat.id,
                           img_link2,
                           caption="روابط ألعاب جمع العملات المعدنية لإستعمالها في خفض السعر لبعض المنتجات، قم بالدخول يوميا لها للحصول على أكبر عدد ممكن في اليوم 👇",
                           reply_markup=keyboard_games)
    except Exception as e:
        print(f"Error in handle_callback_query: {e}")

# Flask app for handling webhook

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'OK', 200

# Start Flask app in a separate thread
def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    # Check if we're running in production (webhook) or development (polling) mode
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if webhook_url:
        # Production mode: Use webhook
        print("🚀 Starting bot in webhook mode...")
        threading.Thread(target=run_flask).start()
        try:
            bot.remove_webhook()
            bot.set_webhook(url=webhook_url)
            print(f"✅ Webhook set to: {webhook_url}")
        except Exception as e:
            print(f"❌ Error setting webhook: {e}")
    else:
        # Development mode: Use polling
        print("🚀 Starting bot in polling mode (development)...")
        try:
            # Remove any existing webhook first
            bot.remove_webhook()
            print("✅ Removed existing webhooks")
            
            # Start polling
            print("🔄 Bot is running... Press Ctrl+C to stop.")
            bot.infinity_polling(none_stop=True, timeout=10, long_polling_timeout=5)
        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user.")
        except Exception as e:
            print(f"❌ Error in polling mode: {e}")
