import html
import requests
import logging
from celery import shared_task
from bs4 import BeautifulSoup
from django.utils import timezone
from decouple import config
from .models import GoldPrice
import pytz
from datetime import datetime
from django.utils.timezone import now

# Load environment variables from .env
TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID")  # Use the channel chat ID (-100xxxxxxxxxx)

def extract_gold_prices(html):
    """Extracts gold prices from the website HTML."""
    soup = BeautifulSoup(html, "html.parser")
    target_titles = {
        "هرگرم طلای 18 عیار": "price-5",
        "هرگرم(طلای آب شده18عیار)": "price-13",
        
    }
    
    prices = {}
    for title, price_id in target_titles.items():
        price_tag = soup.find("div", id=price_id) or soup.find("span", id=price_id)
        if price_tag:
            prices[title] = price_tag.get_text(strip=True)
    
    return prices

@shared_task
def fetch_and_save_gold_prices():
    url = "https://savehzar.ir/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            prices = extract_gold_prices(response.text)
            
            # Only send message if prices have changed
            changed_prices = {}
            for title, new_price in prices.items():
                last_price = GoldPrice.get_last_price(title)
                if last_price != new_price:
                    changed_prices[title] = new_price
                    # Save new price
                    GoldPrice.objects.create(title=title, price=new_price, recorded_at=timezone.now())

            if changed_prices:  # If there are changes, send a message
                message = generate_telegram_message(changed_prices)
                send_telegram_message(message)
        else:
            logging.error(f"Error fetching page: HTTP {response.status_code}")
    except Exception as e:
        logging.error(f"Exception in fetch_and_save_gold_prices: {e}")
        
def generate_telegram_message(prices):
    """Generates a properly formatted Telegram message with corrected titles."""
    tehran_tz = pytz.timezone("Asia/Tehran")
    tehran_time = now().astimezone(tehran_tz).strftime("%H:%M")

    # Title mapping (Website title → Telegram title)
    title_mapping = {
        "هرگرم طلای 18 عیار": "طلای ۱۸ عیار",
        "هرگرم(طلای آب شده18عیار)": "طلای آب شده",  # Fixing this issue
        "هرگرم طلای آب شده18عیار": "طلای آب شده",  # In case extracted differently
    }

    message = f"🕰 ساعت: <b>{now}</b> 🏺\n\n"

    for original_title, price in prices.items():
        # Use mapped title or fallback to the original if no match is found
        telegram_title = title_mapping.get(original_title.strip(), original_title.strip())  
        message += f"📌 <b>{telegram_title}</b>: <code>{price}</code>\n"

    # Add hidden Telegram link
    message += '\n🔗 <a href="https://t.me/tala_faramarzi">طلا و سکه فرامرزی</a>'

    return message






import requests
import logging

def send_telegram_message(message):
    """Sends the gold price update to the Telegram channel with justified text."""
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",  # Ensures bold, normal text, and hidden links work
        "disable_web_page_preview": True  # Prevents link preview
    }

    try:
        result = requests.post(telegram_url, data=payload, timeout=10)
        if result.status_code != 200:
            logging.error(f"Telegram API error: {result.text}")
    except Exception as e:
        logging.error(f"Exception in send_telegram_message: {e}")
