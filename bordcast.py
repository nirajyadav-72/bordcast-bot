import os
import asyncio
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

# Memory temporary database (Data safe rakhne ke liye SQLite use karna behtar hai)
users_db = set()
groups_db = set()

# /start Command Handler
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    chat_id = message.chat.id
    chat_type = message.chat.type

    if chat_type.value == "private":
        users_db.add(chat_id)
        welcome_text = "👋 Hello! Welcome to the Private Chat Bot."
    else:
        groups_db.add(chat_id)
        welcome_text = "👋 Hello! Thanks for adding me to this group."

    await message.reply_text(f"{welcome_text}\n\n👤 **Owner ID:** `{OWNER_ID}`")

# /broadcast Command Handler (Supports Text, Media, Stickers, and GIFs)
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_command(client: Client, message: Message):
    # Check karein ki owner ne kisi message par reply kiya hai ya nahi
    if not message.reply_to_message:
        await message.reply_text("❌ Kisi bhi message, sticker, ya media par reply karke `/broadcast` likhein.")
        return

    broadcast_msg = message.reply_to_message
    status_msg = await message.reply_text("📢 **Broadcast process shuru ho raha hai...**")

    success_users, failed_users = 0, 0
    success_groups, failed_groups = 0, 0

    # 1. Private Users Ko Bhejna
    for user_id in list(users_db):
        try:
            # .copy() method sticker aur har tarah ke media ko support karta hai
            await broadcast_msg.copy(chat_id=user_id)
            success_users += 1
            await asyncio.sleep(0.1)  # Flood restriction se bachne ke liye delay
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await broadcast_msg.copy(chat_id=user_id)
            success_users += 1
        except (UserIsBlocked, PeerIdInvalid):
            users_db.remove(user_id)  # Invalid ya blocked user ko list se hatayein
            failed_users += 1
        except Exception:
            failed_users += 1

    # 2. Groups Ko Bhejna
    for group_id in list(groups_db):
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

    # Final Report Status
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

# Bot run karein
if __name__ == "__main__":
    print("🤖 Media Broadcast Bot successfully chal raha hai...")
    app.run()
      
