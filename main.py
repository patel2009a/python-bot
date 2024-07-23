import requests
from bs4 import BeautifulSoup
import telepot
import re
import os
import json

# Load user data from a JSON file
def load_user_data(file_path='users.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        return {}

# Save user data to a JSON file
def save_user_data(users, file_path='users.json'):
    with open(file_path, 'w') as file:
        json.dump(users, file)

# Initialize bot and user data
bot_token = '7255915165:AAEAl_QGZznRt6yfKe0rrYngQD0dQkuWmEU'
bot = telepot.Bot(bot_token)
users = load_user_data()

# Read sites from a file
def read_sites(file_path):
    with open(file_path, 'r') as file:
        sites = file.readlines()
    return [site.strip() for site in sites]

# Format URL
def format_url(url):
    if not url.startswith('http://') and not url.startswith('https://'):
        return 'http://' + url
    return url

# Check site status
def check_site_status(url):
    try:
        response = requests.get(url, timeout=10)
        return response, None
    except requests.RequestException as e:
        return None, f"Error: {e}"

# Check Cloudflare protection
def check_cloudflare(response):
    return 'cloudflare' in response.headers.get('Server', '').lower()

# Check for CAPTCHA
def check_captcha(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    captcha = soup.find_all(text=re.compile(r'captcha', re.I))
    return bool(captcha)

# Check for payment gateways
def check_payment_gateway(response):
    text = response.text.lower()
    gateways = {
        'stripe': 'Stripe',
        'braintree': 'Braintree',
        'shopify': 'Shopify',
        'paypal': 'PayPal',
        'skrill': 'Skrill',
        'payoneer': 'Payoneer',
        'nab': 'NAB',
        'omise': 'Omise',
        'epay': 'ePay',
        'mastercard': 'Mastercard',
        'visa': 'Visa',
        'discover': 'Discover',
        'american express': 'American Express',
        'adyen': 'Adyen',
        'square': 'Square',
        'authorize.net': 'Authorize.Net',
        '2checkout': '2Checkout',
        'worldpay': 'Worldpay',
        'alipay': 'Alipay',
        'wechat pay': 'WeChat Pay',
        'unionpay': 'UnionPay',
        'apple pay': 'Apple Pay',
        'google pay': 'Google Pay',
        'amazon pay': 'Amazon Pay'
    }
    detected_gateways = [name for keyword, name in gateways.items() if keyword in text]
    return ', '.join(detected_gateways) if detected_gateways else 'Unknown'

# Send a message to a Telegram chat
def send_to_telegram(chat_id, message):
    bot.sendMessage(chat_id, message)

# Command handler for /start
def handle_start(chat_id, user_name):
    if chat_id not in users:
        users[chat_id] = {'name': user_name, 'premium': False}
        save_user_data(users)
    send_to_telegram(chat_id, f"Welcome {user_name}!\nUse /cmds to see available commands.")

# Command handler for /cmds
def handle_cmds(chat_id):
    cmds_message = ("Available commands:\n"
                    "/start - Start interaction with the bot\n"
                    "/cmds - List all commands\n"
                    "/premium - Get premium access\n"
                    "/kick - Remove a user (admin only)\n"
                    "/scan - Scan a file for site status\n")
    send_to_telegram(chat_id, cmds_message)

# Command handler for /premium
def handle_premium(chat_id):
    users[chat_id]['premium'] = True
    save_user_data(users)
    send_to_telegram(chat_id, "You now have premium access!")

# Command handler for /kick
def handle_kick(chat_id, target_chat_id):
    if users[chat_id].get('admin', False):
        if target_chat_id in users:
            del users[target_chat_id]
            save_user_data(users)
            send_to_telegram(chat_id, f"User {target_chat_id} has been kicked.")
        else:
            send_to_telegram(chat_id, "User not found.")
    else:
        send_to_telegram(chat_id, "You are not authorized to perform this action.")

# Command handler for /scan
def handle_scan(chat_id, file_path):
    sites = read_sites(file_path)
    for site in sites:
        formatted_site = format_url(site)
        response, status_message = check_site_status(formatted_site)
        
        if response:
            cloudflare = check_cloudflare(response)
            captcha = check_captcha(response)
            gateway = check_payment_gateway(response)
            
            cloudflare_status = 'Yes 😔' if cloudflare else 'No 🔥'
            captcha_status = 'Yes 😔' if captcha else 'No 🔥'
            overall_status = 'Good 🔥' if not cloudflare and not captcha else 'Not good 😔'
            
            message = (f"Gateways Fetched Successfully ✅\n"
                       f"━━━━━━━━━━━━━━\n"
                       f"➔ Website ⋙ ({site})\n"
                       f"➔ Gateways ⋙ ({gateway})\n"
                       f"➔ Captcha ⋙ ({captcha_status})\n"
                       f"➔ Cloudflare ⋙ ({cloudflare_status})\n"
                       f"➔ Status ⋙ ({overall_status})\n"
                       f"\nBot by - @itsyo3")
        else:
            message = f"Site: {site}\nStatus: {status_message}"
        
        send_to_telegram(chat_id, message)

# Main function to handle incoming messages
def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    user_name = msg['from']['first_name']

    if content_type == 'text':
        text = msg['text']
        if text.startswith('/start'):
            handle_start(chat_id, user_name)
        elif text.startswith('/cmds'):
            handle_cmds(chat_id)
        elif text.startswith('/premium'):
            handle_premium(chat_id)
        elif text.startswith('/kick'):
            parts = text.split()
            if len(parts) == 2:
                target_chat_id = int(parts[1])
                handle_kick(chat_id, target_chat_id)
        elif text.startswith('/scan'):
            handle_scan(chat_id, 'site.txt')
    elif content_type == 'document':
        if users.get(chat_id, {}).get('premium', False):
            file_id = msg['document']['file_id']
            file_path = bot.getFile(file_id)['file_path']
            handle_scan(chat_id, file_path)
        else:
            send_to_telegram(chat_id, "You need to be a premium user to scan files.")

if __name__ == '__main__':
    bot.message_loop(handle)
    print('Bot is listening...')

# To run this bot, make sure to replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token
# and ensure the bot has access to the 'users.json' file for storing user data.
