import requests
import logging
from bs4 import BeautifulSoup
from django.utils import timezone
from celery import shared_task
from decouple import config
from .models import DollorPrice
import pytz
from django.utils.timezone import now

# Load Telegram credentials
TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID")  # Use the channel or group ID

def extract_usd_price(html):
    """Extracts the USD price from Mazaneh.net HTML."""
    soup = BeautifulSoup(html, "html.parser")
    usd_div = soup.find("div", id="USD")
    
    if usd_div:
        price_div = usd_div.find("div", class_="CurrencyPrice")
        if price_div:
            return price_div.get_text(strip=True)
    return None

@shared_task
def fetch_and_save_usd_price():
    url = "https://mazaneh.net/"
    title = "USD"  # Title used in your model to track this value
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            usd_price = extract_usd_price(response.text)
            if usd_price:
                last_price = DollorPrice.get_last_price(title)
                if last_price != usd_price:
                    # Save new USD price to the database
                    DollorPrice.objects.create(title=title, price=usd_price, recorded_at=timezone.now())

                    # Send Telegram message
                    tehran_tz = pytz.timezone("Asia/Tehran")
                    tehran_time = now().astimezone(tehran_tz).strftime("%H:%M")
                    
                    message = (
    f"🕰 ساعت: <b>{tehran_time}</b> 🏺\n\n"
    f"💵 <b>قیمت دلار</b>: <code>{usd_price}</code>\n\n"
    f"🔗 <a href='https://t.me/tala_faramarzi'> طلا و سکه فرامرزی</a>"
)
                    send_telegram_message(message)
        else:
            logging.error(f"Error fetching USD page: HTTP {response.status_code}")
    except Exception as e:
        logging.error(f"Exception in fetch_and_save_usd_price: {e}")

def send_telegram_message(message):
    """Sends the USD price update to the Telegram channel."""
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        result = requests.post(telegram_url, data=payload, timeout=10)
        if result.status_code != 200:
            logging.error(f"Telegram API error: {result.text}")
    except Exception as e:
        logging.error(f"Exception in send_telegram_message: {e}")
