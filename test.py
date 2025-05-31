import requests
from bs4 import BeautifulSoup
from telegram import Bot
import asyncio
import time

# === CONFIGURATION ===
TELEGRAM_TOKEN = '7618039183:AAFnEBqkEnscwEyV3QJGvitbFQ62MnBNzIo'
CHANNEL_ID = '@AKIsMainCh'  # Use '@channelusername' or '-1001234567890' for private channels

bot = Bot(token=TELEGRAM_TOKEN)
last_posted_data = ""

def fetch_grow_garden_stock():
    url = 'https://growagarden.gg/stocks'

    for attempt in range(3):  # Retry up to 3 times
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            break  # Exit loop on success
        except Exception as e:
            print(f"[Attempt {attempt + 1}/3] Error fetching stock:", e)
            time.sleep(2)
    else:
        return ""

    legacy_sections = {
        "🌱 <b>Seed Shop</b>": 'Current Seed Shop Stock in Grow a Garden',
        "🛠 <b>Gear Shop</b>": 'Current Gear Shop Stock in Grow a Garden',
        "🥚 <b>Egg Shop</b>": 'Current Egg Shop Stock in Grow a Garden'
    }

    message_parts = [
        "<pre>┏━━━━━━━━━━━━━━━━━━━━━━┓</pre>",
        "<b>🌼 Grow a Garden Stock Update</b>",
        "<pre>┗━━━━━━━━━━━━━━━━━━━━━━┛</pre>\n"
    ]

    for emoji_title, header_text in legacy_sections.items():
        h3 = soup.find('h3', string=header_text)
        if h3:
            ul = h3.find_next('ul')
            items = [li.get_text(strip=True) for li in ul.find_all('li')] if ul else []
            section_block = (
                f"<pre>┌──────────────────────┐</pre>\n"
                f"{emoji_title}\n" +
                "\n".join(f"• {item}" for item in items) +
                "\n<pre>└──────────────────────┘</pre>\n"
            )
            message_parts.append(section_block)
        else:
            message_parts.append(
                f"<pre>┌──────────────────────┐</pre>\n{emoji_title}\n• Not Found\n<pre>└──────────────────────┘</pre>\n"
            )

    return "\n".join(message_parts).strip()

async def send_stock_to_telegram(message):
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        print("Failed to send message:", e)

async def check_and_post_updates():
    global last_posted_data
    message = fetch_grow_garden_stock()
    if not message:
        print("No stock message built.")
        return

    if message != last_posted_data:
        print("New stock update found. Sending...")
        await send_stock_to_telegram(message)
        last_posted_data = message
    else:
        print("Stock unchanged. No message sent.")

async def main():
    print("Bot started. Checking Grow a Garden stock every 30 seconds.")
    await check_and_post_updates()  # Run once on start
    while True:
        await check_and_post_updates()
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
