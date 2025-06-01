import requests
from bs4 import BeautifulSoup
from telegram import Bot
import asyncio
import time

# === CONFIGURATION ===
TELEGRAM_TOKEN = 'your_bot_token'
CHANNEL_ID = '@AKIsMainCh'
DISCUSSION_ID = -1001234567890  # <- Replace this with your actual discussion group ID

item_notifications = {
    "Carrot": ["@thatkidAki", "@otheruser"],
    "Strawberry": [],
    "Blueberry": [],
    "Orange Tulip": [],
    "Tomato": [],
    "Bamboo": [],
    "Watermelon": [],
    "Apple": [],
    "Pepper": [],
    "Mango": [],
    "Daffodil": [],
    "Pumpkin": [],
    "Corn": [],
    "Coconut": [],
    "Cactus": [],
    "Cacao": [],
    "Dragon Fruit": [],
    "Grape": [],
    "Mushroom": [],
    "Beanstalk": [],
    "Watering Can": [],
    "Trowel": [],
    "Favorite Tool": [],
    "Basic Sprinkler": [],
    "Godly Sprinkler": [],
    "Advanced Sprinkler": [],
    "Master Sprinkler": [],
    "Lightning Rod": [],
    "Recall Wrench": [],
    "Bug Egg": [],
    "Mythic Egg": []
}


bot = Bot(token=TELEGRAM_TOKEN)
last_posted_data = ""

def fetch_grow_garden_stock():
    url = 'https://www.vulcanvalues.com/grow-a-garden/stock'

    for attempt in range(3):
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            break
        except Exception as e:
            print(f"[Attempt {attempt + 1}/3] Error fetching stock:", e)
            time.sleep(2)
    else:
        return "", []

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

    found_items = []

    for header_text, emoji_title in sections.items():
        header = soup.find('h2', string=lambda x: x and header_text in x)
        if header:
            items = []
            sibling = header.find_next_sibling()
            while sibling and sibling.name != 'h2':
                list_items = sibling.find_all('li')
                for li in list_items:
                    item_text = li.get_text(strip=True)
                    if item_text:
                        cleaned = item_text.split(' x')[0].strip()
                        found_items.append(cleaned)
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

    return "\n".join(message_parts).strip(), found_items

async def send_stock_to_telegram(message):
    try:
        sent_msg = await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="HTML", disable_web_page_preview=True)
        return sent_msg.message_id
    except Exception as e:
        print("Failed to send message:", e)
        return None

async def reply_with_mentions(found_items, original_message_id):
    users_to_notify = set()

    for item in found_items:
        if item in item_notifications:
            users_to_notify.update(item_notifications[item])

    if users_to_notify:
        text = "🔔 " + ", ".join(users_to_notify)
        try:
            await bot.send_message(
                chat_id=DISCUSSION_ID,
                text=text,
                reply_to_message_id=original_message_id
            )
            print("✅ Mention reply sent.")
        except Exception as e:
            print("❌ Failed to send reply with mentions:", e)

async def check_and_post_updates():
    global last_posted_data
    message, found_items = fetch_grow_garden_stock()
    if not message:
        print("No stock message built.")
        return

    if message != last_posted_data:
        print("New stock update found. Sending...")
        message_id = await send_stock_to_telegram(message)
        if message_id:
            await reply_with_mentions(found_items, message_id)
        last_posted_data = message
    else:
        print("Stock unchanged. No message sent.")

async def main():
    print("Bot started. Checking Grow a Garden stock every 30 seconds.")
    await check_and_post_updates()
    while True:
        await check_and_post_updates()
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
