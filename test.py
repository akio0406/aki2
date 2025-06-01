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
    url = 'https://www.vulcanvalues.com/grow-a-garden/stock'

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

    # Define the sections to extract
    sections = {
        "SEEDS STOCK": "🌱 Seed Shop",
        "GEAR STOCK": "🛠 Gear Shop",
        "EGG STOCK": "🥚 Egg Shop",
        "HONEY STOCK": "🐝 Bee Event Stock",
        "COSMETICS STOCK": "🎀 Cosmetics Shop"
    }

    message_parts = [
        "<pre>┏━━━━━━━━━━━━━━━━━━━━━━┓</pre>",
        "<b>🌼 Grow a Garden Stock Update</b>",
        "<pre>┗━━━━━━━━━━━━━━━━━━━━━━┛</pre>\n"
    ]

    for header_text, emoji_title in sections.items():
        header = soup.find('h2', string=lambda x: x and header_text in x)
        if header:
            items = []
            # Find the next sibling elements containing the stock items
            sibling = header.find_next_sibling()
            while sibling and sibling.name != 'h2':
                # Look for list items within the sibling
                list_items = sibling.find_all('li')
                for li in list_items:
                    item_text = li.get_text(strip=True)
                    if item_text:
                        items.append(f"• {item_text}")
                sibling = sibling.find_next_sibling()
            if items:
                section_block = (
                    f"<pre>┌──────────────────────┐</pre>\n"
                    f"{emoji_title}\n" +
                    "\n".join(items) +
                    "\n<pre>└──────────────────────┘</pre>\n"
                )
                message_parts.append(section_block)
            else:
                message_parts.append(
                    f"<pre>┌──────────────────────┐</pre>\n{emoji_title}\n• Not Found\n<pre>└──────────────────────┘</pre>\n"
                )
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
