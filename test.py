import requests
from bs4 import BeautifulSoup
from telegram import Bot
import asyncio
import time

# === CONFIGURATION ===
TELEGRAM_TOKEN = '7618039183:AAFnEBqkEnscwEyV3QJGvitbFQ62MnBNzIo'
DISCUSSION_ID = -1002534125875  # Your discussion group ID

# Item → list of users to notify
item_notifications = {
    "Carrot": [],
    "Strawberry": [],
    "Blueberry": [],
    "Orange Tulip": [],
    "Tomato": [],
    "Bamboo": [],
    "Watermelon": [],
    "Apple": [],
    "Pepper": ["@thatkidAki"],
    "Mango": [],
    "Daffodil": [],
    "Pumpkin": [],
    "Corn": [],
    "Coconut": [],
    "Cactus": [],
    "Cacao": ["@eeevee2", "@thatkidAki"],
    "Dragon Fruit": [],
    "Grape": [],
    "Mushroom": ["@thatkidAki"],
    "Beanstalk": ["@eeevee2", "@thatkidAki"],
    "Watering Can": [],
    "Trowel": [],
    "Favorite Tool": [],
    "Basic Sprinkler": [],
    "Godly Sprinkler": ["@thatkidAki"],
    "Advanced Sprinkler": ["@thatkidAki"],
    "Master Sprinkler": ["@eeevee2", "@thatkidAki"],
    "Lightning Rod": ["@eeevee2", "@thatkidAki"],
    "Recall Wrench": [],
    "Bug Egg": [],
    "Mythic Egg": []
}

bot = Bot(token=TELEGRAM_TOKEN)
last_posted_data = ""

def fetch_grow_garden_stock():
    arcaiuz_url = 'https://arcaiuz.com/grow-a-garden-stock'
    vulcan_url = 'https://www.vulcanvalues.com/grow-a-garden/stock'

    # --- Get Weather ---
    try:
        arc_response = requests.get(arcaiuz_url, timeout=10)
        arc_response.raise_for_status()
        arc_soup = BeautifulSoup(arc_response.text, 'html.parser')

        weather_div = arc_soup.find('div', string=lambda x: x and "Weather" in x)
        if not weather_div:
            weather_text = ""
        else:
            weather_text = weather_div.find_next().get_text(strip=True)
    except Exception as e:
        print("⚠️ Failed to fetch weather:", e)
        weather_text = ""

    if not weather_text:
        return "", []

    # --- Get Stock ---
    try:
        response = requests.get(vulcan_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print("⚠️ Failed to fetch stock:", e)
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
        f"<b>🌼 Grow a Garden Stock Update</b>",
        f"<b>🌦️ Weather: {weather_text}</b>",
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
                        cleaned = item_text.split('x')[0].strip()
                        found_items.append(cleaned)
                        items.append(f"• {item_text}")
                sibling = sibling.find_next_sibling()
            section_block = (
                f"<pre>┌──────────────────────┐</pre>\n"
                f"{emoji_title}\n" +
                ("\n".join(items) if items else "• Not Found") +
                "\n<pre>└──────────────────────┘</pre>\n"
            )
            message_parts.append(section_block)
        else:
            message_parts.append(
                f"<pre>┌──────────────────────┐</pre>\n{emoji_title}\n• Not Found\n<pre>└──────────────────────┘</pre>\n"
            )

    return "\n".join(message_parts).strip(), found_items

async def send_mentions_to_discussion(found_items):
    user_items = {}

    for item in found_items:
        for user in item_notifications.get(item, []):
            user_items.setdefault(user, []).append(item)

    if not user_items:
        print("ℹ️ No users to notify.")
        return

    message_blocks = []
    for user, items in user_items.items():
        if not items:
            continue
        box_width = max(len(user), max(len(i) for i in items)) + 4
        top = f"┏{'━' * box_width}┓"
        bottom = f"┗{'━' * box_width}┛"
        user_line = f"{user}".ljust(box_width)
        item_lines = [f"┣ {item}" for item in items]
        block = "\n".join([top, user_line] + item_lines + [bottom])
        message_blocks.append(block)

    try:
        await bot.send_message(
            chat_id=DISCUSSION_ID,
            text="\n\n".join(message_blocks),
            parse_mode="HTML"
        )
        print("✅ Stylish mention message sent to discussion.")
    except Exception as e:
        print("❌ Failed to send stylish mention message:", e)

async def check_and_post_updates():
    global last_posted_data
    message, found_items = fetch_grow_garden_stock()
    if not message:
        print("⛅ No weather or stock message available. Skipping.")
        return

    if message != last_posted_data:
        print("📢 New stock + weather update. Sending...")

        try:
            await bot.send_message(
                chat_id=DISCUSSION_ID,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            print("✅ Stock update sent to discussion.")
        except Exception as e:
            print("❌ Failed to send stock update:", e)

        await send_mentions_to_discussion(found_items)
        last_posted_data = message
    else:
        print("⏸ No change. Waiting...")

async def main():
    print("🔁 Bot started. Checking every second...")
    await check_and_post_updates()
    while True:
        await check_and_post_updates()
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
