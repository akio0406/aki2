import requests
from bs4 import BeautifulSoup
from telegram import Bot
import asyncio
import time

# === CONFIGURATION ===
TELEGRAM_TOKEN = '7618039183:AAFnEBqkEnscwEyV3QJGvitbFQ62MnBNzIo'
DISCUSSION_ID = -1002534125875  # Your discussion group ID

item_notifications = {
    "Carrot": [],
    "Strawberry": [],
    "Blueberry": [],
    "Orange Tulip": [],
    "Tomato": [],
    "Bamboo": [],
    "Watermelon": [],
    "Apple": [],
    "Pepper": ["@thatkidAki", "@zyrillkyato1", "@eeevee2"],
    "Mango": [],
    "Daffodil": [],
    "Pumpkin": [],
    "Corn": [],
    "Coconut": [],
    "Cactus": [],
    "Cacao": ["@eeevee2", "@thatkidAki", "@kamonohashi12", "@zyrillkyato1"],
    "Dragon Fruit": [],
    "Grape": ["@kamonohashi12"],
    "Mushroom": ["@thatkidAki", "@zyrillkyato1"],
    "Beanstalk": ["@eeevee2", "@thatkidAki", "@kamonohashi12", "@zyrillkyato1"],
    "Watering Can": [],
    "Trowel": [],
    "Favorite Tool": [],
    "Basic Sprinkler": ["@supremo_deprimo"],
    "Godly Sprinkler": ["@thatkidAki", "@kamonohashi12", "@supremo_deprimo", "@eeevee2"],
    "Advanced Sprinkler": ["@thatkidAki", "@supremo_deprimo", "@eeevee2"],
    "Master Sprinkler": ["@eeevee2", "@thatkidAki", "@kamonohashi12", "@zyrillkyato1", "@supremo_deprimo"],
    "Lightning Rod": ["@eeevee2", "@thatkidAki"],
    "Recall Wrench": [],
    "Bug Egg": [],
    "Mythic Egg": []
}

bot = Bot(token=TELEGRAM_TOKEN)
last_posted_data = ""
last_found_items = set()
last_stock_message_id = None
last_mentions_message_id = None

def fetch_grow_garden_stock():
    url = 'https://www.vulcanvalues.com/grow-a-garden/stock'
    for _ in range(3):
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            break
        except:
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

async def send_mentions_to_discussion(newly_appeared_items):
    global last_mentions_message_id

    user_items = {}
    for item in newly_appeared_items:
        for user in item_notifications.get(item, []):
            user_items.setdefault(user, []).append(item)

    if not user_items:
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
        if last_mentions_message_id:
            try:
                await bot.delete_message(chat_id=DISCUSSION_ID, message_id=last_mentions_message_id)
            except:
                pass

        sent_msg = await bot.send_message(
            chat_id=DISCUSSION_ID,
            text="\n\n".join(message_blocks),
            parse_mode="HTML"
        )
        last_mentions_message_id = sent_msg.message_id
    except:
        pass

async def check_and_post_updates():
    global last_posted_data, last_found_items, last_stock_message_id

    message, current_found_items = fetch_grow_garden_stock()
    if not message:
        return

    current_found_set = set(current_found_items)
    new_items = current_found_set - last_found_items

    if message != last_posted_data:
        if last_stock_message_id:
            try:
                await bot.delete_message(chat_id=DISCUSSION_ID, message_id=last_stock_message_id)
            except:
                pass

        try:
            sent_msg = await bot.send_message(
                chat_id=DISCUSSION_ID,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            last_stock_message_id = sent_msg.message_id
        except:
            pass

        await send_mentions_to_discussion(new_items)
        last_posted_data = message
        last_found_items = current_found_set

async def main():
    await check_and_post_updates()
    while True:
        await check_and_post_updates()
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
