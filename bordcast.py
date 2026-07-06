import os
import asyncio
import sqlite3
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, PeerIdInvalid

# .env file load karein
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

app = Client("broadcast_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# SQLite Database Setup (Permanent Storage)
DB_FILE = "bot_database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

# Database se data fetch aur insert karne ke functions
def add_user(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
    finally:
        conn.close()

def add_group(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO groups (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
    finally:
        conn.close()

def remove_user(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))
        conn.commit()
    finally:
        conn.close()

def get_all_chats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT chat_id FROM users")
        users = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT chat_id FROM groups")
        groups = [row[0] for row in cursor.fetchall()]
        return users, groups
    finally:
        conn.close()

# Initialize DB on startup
init_db()

# /start Command Handler
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    chat_id = message.chat.id
    chat_type = message.chat.type

    if chat_type.value == "private":
        add_user(chat_id)
        welcome_text = "👋 Hello! Welcome to the quiz Bot."
    else:
        add_group(chat_id)
        welcome_text = "👋 Hello! Thanks for adding me to this group."

    await message.reply_text(f"{welcome_text}")

# /broadcast Command Handler
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_command(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("❌ Kisi bhi message, sticker, ya media par reply karke `/broadcast` likhein.")
        return

    broadcast_msg = message.reply_to_message
    status_msg = await message.reply_text("📢 **Broadcast process shuru ho raha hai...**")

    # Database se active lists nikalein
    users_list, groups_list = get_all_chats()

    success_users, failed_users = 0, 0
    success_groups, failed_groups = 0, 0

    # 1. Users ko broadcast bhejna
    for user_id in users_list:
        try:
            await broadcast_msg.copy(chat_id=user_id)
            success_users += 1
            await asyncio.sleep(0.1)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await broadcast_msg.copy(chat_id=user_id)
            success_users += 1
        except (UserIsBlocked, PeerIdInvalid):
            remove_user(user_id)  # Blocked users ko DB se permanent hatayein
            failed_users += 1
        except Exception:
            failed_users += 1

    # 2. Groups ko broadcast bhejna
    for group_id in groups_list:
        try:
            await broadcast_msg.copy(chat_id=group_id)
            success_groups += 1
            await asyncio.sleep(0.1)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await broadcast_msg.copy(chat_id=group_id)
            success_groups += 1
        except Exception:
            failed_groups += 1

    # Final Summary Report
    report = (
        "📊 **Broadcast Report:**\n\n"
        "👤 **Private Chats:**\n"
        f"✅ Success: {success_users}\n"
        f"❌ Failed/Blocked: {failed_users}\n\n"
        "👥 **Groups:**\n"
        f"✅ Success: {success_groups}\n"
        f"❌ Failed: {failed_groups}"
    )
    await status_msg.edit_text(report)

if __name__ == "__main__":
    print("🤖 Database Broadcast Bot successfully chal raha hai...")
    app.run()
            
