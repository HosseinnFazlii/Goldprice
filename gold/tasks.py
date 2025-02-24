import requests
import logging
from celery import shared_task
from bs4 import BeautifulSoup
from django.utils import timezone
from decouple import config
from .models import GoldPrice

# Load environment variables from .env
TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID")  # Use the channel chat ID (-100xxxxxxxxxx)

def extract_gold_prices(html):
    """Extracts gold prices from the website HTML."""
    soup = BeautifulSoup(html, "html.parser")
    target_titles = {
        "هرگرم طلای 18 عیار": "price-5",
        "هرگرم (طلای آب شده18عیار)": "price-13",
        
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
            if prices:
                message = generate_telegram_message(prices)

                # Save prices to the database
                for title, price in prices.items():
                    GoldPrice.objects.create(title=title, price=price, recorded_at=timezone.now())

                # Send the message to Telegram channel
                send_telegram_message(message)
        else:
            logging.error(f"Error fetching page: HTTP {response.status_code}")
    except Exception as e:
        logging.error(f"Exception in fetch_and_save_gold_prices: {e}")

def generate_telegram_message(prices):
    """Generates a formatted Telegram message with gold prices."""
    message = "📢 **آپدیت قیمت طلا و سکه** 📢\n\n"
    for title, price in prices.items():
        message += f"🔹 {title}: `{price}` تومان\n"
    message += "\n⏳ به‌روز شده: " + timezone.now().strftime("%Y-%m-%d %H:%M")
    return message

def send_telegram_message(message):
    """Sends the gold price update to the Telegram channel."""
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"  # Enables formatting in the message
    }
    try:
        result = requests.post(telegram_url, data=payload, timeout=10)
        if result.status_code != 200:
            logging.error(f"Telegram API error: {result.text}")
    except Exception as e:
        logging.error(f"Exception in send_telegram_message: {e}")
