"""
Full Selling Bot — Simplified Version
Author: Generated for Aryan
Date: 2025-11-18
"""

import os
import time
import sqlite3
import threading
import html
import logging
from typing import List, Tuple, Optional

from telebot import TeleBot, types
from telebot.types import Message

# --------------------------
# CONFIGURATION
# --------------------------
BOT_TOKEN = "8592311790:AAGpmgitTmbN9OV5vvQhe9N7t0CFImxWCI0"
ADMIN_USERNAME = "Premium_Pro_Seller"
ADMIN_CHAT_ID = 7504156532

# Secret admin command strings
CMD_APPROVE = "/aman7004"
CMD_APPROVE_ALL = "/aman7004a"
CMD_DISAPPROVE = "/aman7004d"
CMD_DISAPPROVE_ALL = "/aman7004dd"
CMD_ADD = "/aman7004+"
CMD_REMOVE = "/aman7004-"
CMD_UPDATE = "/aman7004u"
CMD_ANNOUNCE = "/aman7004tell"
CMD_STATS = "/aman7004ls"

# Flood control delays
SEND_DELAY = 0.35
SHORT_DELAY = 0.12

# SQLite DB file
DB_FILE = "materials.db"

# Telebot parse mode
PARSE_MODE = "HTML"

# --------------------------
# LOGGING
# --------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------
# INITIALIZE TELEBOT
# --------------------------
bot = TeleBot(BOT_TOKEN, parse_mode=PARSE_MODE)

# --------------------------
# DATABASE (SQLite) SETUP
# --------------------------
db_lock = threading.Lock()

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        keyword TEXT PRIMARY KEY,
        price TEXT,
        description TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        saved_message_id INTEGER,
        order_index INTEGER,
        content_type TEXT,
        FOREIGN KEY (keyword) REFERENCES materials(keyword)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS demo_contents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        saved_message_id INTEGER,
        order_index INTEGER,
        content_type TEXT,
        FOREIGN KEY (keyword) REFERENCES materials(keyword)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS approvals (
        user_id INTEGER,
        keyword TEXT,
        UNIQUE(user_id, keyword)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    return conn

db_conn = init_db()

# --------------------------
# DATABASE UTILITIES
# --------------------------
def add_user(user_id: int, username: str, first_name: str, last_name: str):
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users(user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                    (user_id, username, first_name, last_name))
        db_conn.commit()

def get_all_users():
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("SELECT user_id FROM users")
        return [row[0] for row in cur.fetchall()]

def get_user_count():
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        return cur.fetchone()[0]

def get_approved_users():
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("SELECT DISTINCT user_id FROM approvals")
        return [row[0] for row in cur.fetchall()]

def get_vip_users():
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("SELECT DISTINCT user_id FROM approvals WHERE keyword IS NULL")
        return [row[0] for row in cur.fetchall()]

def add_material_db(keyword: str, price: str, description: str):
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("INSERT OR REPLACE INTO materials(keyword, price, description) VALUES (?, ?, ?)",
                    (keyword.lower(), price, description))
        db_conn.commit()

def remove_material_db(keyword: str):
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("DELETE FROM materials WHERE keyword = ?", (keyword.lower(),))
        cur.execute("DELETE FROM contents WHERE keyword = ?", (keyword.lower(),))
        cur.execute("DELETE FROM demo_contents WHERE keyword = ?", (keyword.lower(),))
        db_conn.commit()

def update_material_field_db(keyword: str, field: str, value: str) -> bool:
    if field not in ("price", "description"):
        return False
    with db_lock:
        cur = db_conn.cursor()
        cur.execute(f"UPDATE materials SET {field} = ? WHERE keyword = ?", (value, keyword.lower()))
        db_conn.commit()
        return cur.rowcount > 0

def get_material_list() -> List[Tuple[str,str,str]]:
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("SELECT keyword, price, description FROM materials ORDER BY keyword ASC")
        return cur.fetchall()

def get_material(keyword: str) -> Optional[Tuple[str,str,str]]:
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("SELECT keyword, price, description FROM materials WHERE keyword = ?", (keyword.lower(),))
        return cur.fetchone()

def add_content_entry_db(keyword: str, saved_message_id: int, order_index: int, content_type: str="unknown", is_demo: bool=False):
    with db_lock:
        cur = db_conn.cursor()
        table = "demo_contents" if is_demo else "contents"
        cur.execute(f"INSERT INTO {table}(keyword, saved_message_id, order_index, content_type) VALUES (?, ?, ?, ?)",
                    (keyword.lower(), int(saved_message_id), int(order_index), content_type))
        db_conn.commit()

def delete_content_entry_db(keyword: str, saved_message_id: Optional[int]=None, is_demo: bool=False):
    with db_lock:
        cur = db_conn.cursor()
        table = "demo_contents" if is_demo else "contents"
        if saved_message_id:
            cur.execute(f"DELETE FROM {table} WHERE keyword = ? AND saved_message_id = ?", (keyword.lower(), int(saved_message_id)))
        else:
            cur.execute(f"DELETE FROM {table} WHERE keyword = ?", (keyword.lower(),))
        db_conn.commit()

def get_material_contents(keyword: str, is_demo: bool=False) -> List[int]:
    with db_lock:
        cur = db_conn.cursor()
        table = "demo_contents" if is_demo else "contents"
        cur.execute(f"SELECT saved_message_id FROM {table} WHERE keyword = ? ORDER BY order_index ASC", (keyword.lower(),))
        return [row[0] for row in cur.fetchall()]

def get_next_order_index(keyword: str, is_demo: bool=False) -> int:
    with db_lock:
        cur = db_conn.cursor()
        table = "demo_contents" if is_demo else "contents"
        cur.execute(f"SELECT COALESCE(MAX(order_index), 0) FROM {table} WHERE keyword = ?", (keyword.lower(),))
        row = cur.fetchone()
        return (row[0] or 0) + 1

def approve_user_for_keyword(user_id: int, keyword: str):
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("INSERT OR IGNORE INTO approvals(user_id, keyword) VALUES (?, ?)", (int(user_id), keyword.lower()))
        db_conn.commit()

def disapprove_user_for_keyword(user_id: int, keyword: str):
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("DELETE FROM approvals WHERE user_id = ? AND keyword = ?", (int(user_id), keyword.lower()))
        db_conn.commit()

def approve_user_global(user_id: int):
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("INSERT OR IGNORE INTO approvals(user_id, keyword) VALUES (?, NULL)", (int(user_id),))
        db_conn.commit()

def disapprove_user_all(user_id: int):
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("DELETE FROM approvals WHERE user_id = ?", (int(user_id),))
        db_conn.commit()

def user_is_approved_for(user_id: int, keyword: str) -> bool:
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("SELECT 1 FROM approvals WHERE user_id = ? AND keyword IS NULL", (int(user_id),))
        if cur.fetchone():
            return True
        cur.execute("SELECT 1 FROM approvals WHERE user_id = ? AND keyword = ?", (int(user_id), keyword.lower()))
        return cur.fetchone() is not None

# --------------------------
# ADMIN STATE MACHINE
# --------------------------
admin_states = {}

def start_adding_flow(admin_chat_id: int, keyword: str, price: str):
    admin_states[admin_chat_id] = {
        "mode": "adding",
        "step": "awaiting_description",
        "keyword": keyword.lower(),
        "price": price,
        "description": "",
        "collected_saved_message_ids": [],
        "collected_demo_message_ids": [],
        "next_order_index": get_next_order_index(keyword.lower()),
        "demo_next_order_index": get_next_order_index(keyword.lower(), is_demo=True)
    }

def start_updating_flow(admin_chat_id: int, keyword: str):
    admin_states[admin_chat_id] = {
        "mode": "updating",
        "step": "awaiting_update_choice",
        "keyword": keyword.lower(),
        "collected_saved_message_ids": [],
        "collected_demo_message_ids": [],
        "next_order_index": get_next_order_index(keyword.lower()),
        "demo_next_order_index": get_next_order_index(keyword.lower(), is_demo=True)
    }

def reset_admin_state(admin_chat_id: int):
    if admin_chat_id in admin_states:
        del admin_states[admin_chat_id]

# --------------------------
# UTILITY FUNCTIONS
# --------------------------
def send_long_text_split(chat_id: int, text: str, chunk_chars: int=3500):
    if not text:
        return
    remaining = text
    while remaining:
        part = remaining[:chunk_chars]
        remaining = remaining[chunk_chars:]
        bot.send_message(chat_id, part)
        time.sleep(SHORT_DELAY)

def bot_forward_to_admin_chat(from_chat_id: int, message_id: int) -> Optional[int]:
    try:
        forwarded_msg = bot.forward_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=from_chat_id,
            message_id=message_id
        )
        
        if forwarded_msg and hasattr(forwarded_msg, 'message_id'):
            logger.info(f"Successfully forwarded message {message_id} to admin chat as {forwarded_msg.message_id}")
            return forwarded_msg.message_id
        else:
            logger.error("No message_id returned from forward operation")
            return None
            
    except Exception as e:
        logger.exception("Error forwarding message %s to admin chat: %s", message_id, e)
        return None

def capture_saved_message_id_from_admin_message(message: Message) -> Optional[Tuple[int, str]]:
    try:
        content_type = message.content_type
        saved_message_id = bot_forward_to_admin_chat(message.chat.id, message.message_id)
        
        if saved_message_id:
            logger.info(f"Successfully captured content: Message ID {saved_message_id}, Type: {content_type}")
            return (saved_message_id, content_type)
        else:
            logger.error("Failed to forward message to admin chat")
            return None
            
    except Exception as e:
        logger.exception("Error in capture_saved_message_id_from_admin_message: %s", e)
        return None

def parse_command_and_args(text: str):
    parts = text.strip().split()
    cmd = parts[0] if parts else ""
    args = parts[1:]
    return cmd, args

def send_product_list(chat_id: int, user_id: int):
    materials = get_material_list()
    if not materials:
        bot.send_message(chat_id, "📭 No materials available yet.")
        return
    
    # Count accessible materials
    accessible_count = 0
    for kw, _, _ in materials:
        if user_is_approved_for(user_id, kw):
            accessible_count += 1
    
    # Send initial message
    if accessible_count > 0:
        bot.send_message(chat_id, f"🎁 You have access to {accessible_count} out of {len(materials)} materials!")
    else:
        bot.send_message(chat_id, "🔒 You don't have access to any material yet.")
    
    # Send product list
    for keyword, price, desc in materials:
        is_approved = user_is_approved_for(user_id, keyword)
        status = "✅ (Approved)" if is_approved else "❌ (Not Approved)"
        text = f"<b>{html.escape(keyword)}</b>\n💰 Price: {html.escape(price)}\n📝 {html.escape(desc)}\n{status}"
        send_long_text_split(chat_id, text)
        time.sleep(SHORT_DELAY)
    
    if accessible_count == 0:
        bot.send_message(chat_id, f"👤 Contact admin for approval: @{ADMIN_USERNAME}")

def send_broadcast_message(message: Message):
    """Send announcement to all users"""
    users = get_all_users()
    success_count = 0
    fail_count = 0
    
    bot.send_message(ADMIN_CHAT_ID, f"📢 Starting broadcast to {len(users)} users...")
    
    for user_id in users:
        try:
            if message.content_type == 'text':
                send_long_text_split(user_id, message.text)
            else:
                bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=ADMIN_CHAT_ID,
                    message_id=message.message_id
                )
            success_count += 1
            time.sleep(SEND_DELAY)
        except Exception as e:
            logger.error(f"Failed to send to user {user_id}: {e}")
            fail_count += 1
            time.sleep(0.5)
    
    bot.send_message(ADMIN_CHAT_ID, f"✅ Broadcast completed!\nSuccess: {success_count}\nFailed: {fail_count}")

# --------------------------
# BOT COMMAND HANDLERS
# --------------------------
@bot.message_handler(commands=['start'])
def handle_start(message: Message):
    user = message.from_user
    chat_id = message.chat.id
    
    # Add user to database
    add_user(user.id, user.username, user.first_name, user.last_name)
    
    # Send welcome message
    welcome_text = (
        "👋 Welcome to our Material Store!\n\n"
        "📚 Here you will get many materials in various price ranges.\n\n"
        "Below are the currently available materials:"
    )
    bot.send_message(chat_id, welcome_text)
    time.sleep(SHORT_DELAY)
    
    # Send product list
    send_product_list(chat_id, user.id)

@bot.message_handler(commands=['product'])
def handle_product(message: Message):
    user = message.from_user
    chat_id = message.chat.id
    
    bot.send_message(chat_id, "🛍️ Available Products:")
    send_product_list(chat_id, user.id)
    
    # Additional instruction
    contact_text = (
        f"\n💡 To get access to any product, contact our admin:\n"
        f"👤 @{ADMIN_USERNAME}\n\n"
        f"Send them the keyword of the product you're interested in!"
    )
    bot.send_message(chat_id, contact_text)

@bot.message_handler(commands=['help'])
def handle_help(message: Message):
    help_text = (
        "🤖 <b>Bot Help Guide</b>\n\n"
        "📋 <b>Available Commands:</b>\n"
        "/start - Start the bot and see available materials\n"
        "/product - View all available products\n"
        "/demo - Get a demo of any product\n"
        "/get - Get full material if approved\n\n"
        
        "🛒 <b>How to Buy:</b>\n"
        "1. Use /product to see available materials\n"
        "2. Note the keyword of material you want\n"
        "3. Contact admin @{ADMIN_USERNAME} for approval\n"
        "4. Once approved, use /get with the keyword\n\n"
        
        "🎬 <b>Demo Feature:</b>\n"
        "Use /demo to request a demo of any material before purchasing\n\n"
        
        "📦 <b>Getting Materials:</b>\n"
        "After approval, use /get <keyword> to receive your materials\n\n"
        
        "❓ <b>Need Help?</b>\n"
        "Contact @{ADMIN_USERNAME} for any questions"
    ).format(ADMIN_USERNAME=ADMIN_USERNAME)
    
    send_long_text_split(message.chat.id, help_text)

@bot.message_handler(commands=['demo'])
def handle_demo(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Show available products first
    materials = get_material_list()
    if not materials:
        bot.send_message(chat_id, "📭 No materials available for demo yet.")
        return
    
    bot.send_message(chat_id, "🎬 <b>Demo Materials Available:</b>")
    for keyword, price, desc in materials:
        text = f"<b>{html.escape(keyword)}</b>\n💰 Price: {html.escape(price)}\n📝 {html.escape(desc)}"
        send_long_text_split(chat_id, text)
        time.sleep(SHORT_DELAY)
    
    # Ask for keyword
    bot.send_message(chat_id, "🔍 Enter the keyword of the product you want a demo for:")
    
    # Set state for demo request
    admin_states[chat_id] = {
        "mode": "user_demo",
        "step": "awaiting_demo_keyword"
    }

@bot.message_handler(commands=['get'])
def handle_get(message: Message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    if ' ' in text:
        # Direct keyword provided
        keyword = text.split(' ', 1)[1].strip().lower()
        send_material_to_user(chat_id, message.from_user.id, keyword)
    else:
        # Ask for keyword
        bot.send_message(chat_id, "🔍 Enter the keyword of the material you want:")
        admin_states[chat_id] = {
            "mode": "user_get",
            "step": "awaiting_get_keyword"
        }

def send_material_to_user(chat_id: int, user_id: int, keyword: str):
    mat = get_material(keyword)
    if not mat:
        bot.send_message(chat_id, "❌ Invalid keyword. Use /product to see available materials.")
        return
    
    if not user_is_approved_for(user_id, keyword):
        bot.send_message(chat_id, f"❌ You are not approved for <b>{html.escape(keyword)}</b>\nContact admin: @{ADMIN_USERNAME}")
        return
    
    saved_message_ids = get_material_contents(keyword)
    if not saved_message_ids:
        bot.send_message(chat_id, "📭 This material has no content stored yet.")
        return
    
    try:
        bot.send_message(chat_id, f"📦 Preparing {len(saved_message_ids)} items for <b>{html.escape(keyword)}</b>...")
        for msg_id in saved_message_ids:
            bot.forward_message(
                chat_id=chat_id,
                from_chat_id=ADMIN_CHAT_ID,
                message_id=msg_id
            )
            time.sleep(SEND_DELAY)
        bot.send_message(chat_id, f"✅ Delivery complete! Material: <b>{html.escape(keyword)}</b>")
    except Exception as e:
        logger.exception("Error forwarding messages: %s", e)
        bot.send_message(chat_id, "❌ Failed to send content. Contact admin.")

def send_demo_to_user(chat_id: int, keyword: str):
    demo_message_ids = get_material_contents(keyword, is_demo=True)
    if not demo_message_ids:
        bot.send_message(chat_id, "🎬 No demo content available for this material.")
        return
    
    try:
        bot.send_message(chat_id, f"🎬 Sending demo for <b>{html.escape(keyword)}</b>...")
        for msg_id in demo_message_ids:
            bot.forward_message(
                chat_id=chat_id,
                from_chat_id=ADMIN_CHAT_ID,
                message_id=msg_id
            )
            time.sleep(SEND_DELAY)
        bot.send_message(chat_id, f"✅ Demo complete! Contact admin to get full access: @{ADMIN_USERNAME}")
    except Exception as e:
        logger.exception("Error sending demo: %s", e)
        bot.send_message(chat_id, "❌ Failed to send demo. Contact admin.")

# --------------------------
# ADMIN COMMAND HANDLERS
# --------------------------
@bot.message_handler(func=lambda m: m and m.text and m.text.strip().split()[0] in (
    CMD_APPROVE, CMD_APPROVE_ALL, CMD_DISAPPROVE, CMD_DISAPPROVE_ALL, 
    CMD_ADD, CMD_REMOVE, CMD_UPDATE, CMD_ANNOUNCE, CMD_STATS
))
def handle_secret_admin_commands(message: Message):
    chat_id = message.chat.id
    text = message.text.strip()
    cmd, args = parse_command_and_args(text)

    if cmd == CMD_APPROVE:
        if len(args) < 2:
            bot.reply_to(message, "Usage: /aman7004 <user_chat_id> <keyword>\nExample: /aman7004 123456789 physics_notes")
            return
        try:
            target_user_id = int(args[0])
        except:
            bot.reply_to(message, "Invalid user_chat_id. It must be numeric.")
            return
        keyword = args[1]
        if not get_material(keyword):
            bot.reply_to(message, "Invalid keyword. Use /product to see available keywords.")
            return
        approve_user_for_keyword(target_user_id, keyword)
        bot.reply_to(message, f"✅ Approved user {target_user_id} for keyword <b>{html.escape(keyword)}</b>.")
        return

    if cmd == CMD_APPROVE_ALL:
        if len(args) < 1:
            bot.reply_to(message, "Usage: /aman7004a <user_chat_id>\nExample: /aman7004a 123456789")
            return
        try:
            target_user_id = int(args[0])
        except:
            bot.reply_to(message, "Invalid user_chat_id. It must be numeric.")
            return
        approve_user_global(target_user_id)
        bot.reply_to(message, f"✅ Approved user {target_user_id} for ALL materials.")
        return

    if cmd == CMD_DISAPPROVE:
        if len(args) < 2:
            bot.reply_to(message, "Usage: /aman7004d <user_chat_id> <keyword>\nExample: /aman7004d 123456789 physics_notes")
            return
        try:
            target_user_id = int(args[0])
        except:
            bot.reply_to(message, "Invalid user_chat_id. It must be numeric.")
            return
        keyword = args[1]
        disapprove_user_for_keyword(target_user_id, keyword)
        bot.reply_to(message, f"❌ Disapproved user {target_user_id} for keyword <b>{html.escape(keyword)}</b>.")
        return

    if cmd == CMD_DISAPPROVE_ALL:
        if len(args) < 1:
            bot.reply_to(message, "Usage: /aman7004dd <user_chat_id>\nExample: /aman7004dd 123456789")
            return
        try:
            target_user_id = int(args[0])
        except:
            bot.reply_to(message, "Invalid user_chat_id. It must be numeric.")
            return
        disapprove_user_all(target_user_id)
        bot.reply_to(message, f"❌ Removed all approvals for user {target_user_id}.")
        return

    if cmd == CMD_ADD:
        if len(args) < 2:
            bot.reply_to(message, "Usage: /aman7004+ <keyword> <price>\nExample: /aman7004+ physics_notes 199")
            return
        keyword = args[0]
        price = " ".join(args[1:])
        start_adding_flow(chat_id, keyword, price)
        bot.reply_to(message, "📝 Send the description for this material.")
        return

    if cmd == CMD_REMOVE:
        if len(args) < 1:
            bot.reply_to(message, "Usage: /aman7004- <keyword>\nExample: /aman7004- physics_notes")
            return
        keyword = args[0]
        if not get_material(keyword):
            bot.reply_to(message, "❌ Invalid keyword — not found.")
            return
        remove_material_db(keyword)
        bot.reply_to(message, f"🗑️ Material <b>{html.escape(keyword)}</b> removed from the database.")
        return

    if cmd == CMD_UPDATE:
        if len(args) < 1:
            bot.reply_to(message, "Usage: /aman7004u <keyword>\nExample: /aman7004u physics_notes")
            return
        keyword = args[0]
        if not get_material(keyword):
            bot.reply_to(message, "❌ Invalid keyword — not found.")
            return
        start_updating_flow(chat_id, keyword)
        bot.reply_to(message, ("🔄 What would you like to update?\nOptions:\n"
                               "• price\n"
                               "• description\n"
                               "• add_content\n"
                               "• delete_content\n"
                               "• add_demo\n"
                               "• delete_demo\n\n"
                               "Send exactly one option"))
        return

    if cmd == CMD_ANNOUNCE:
        if not args:
            bot.reply_to(message, "Usage: /aman7004tell <message>\nOr reply to a message with /aman7004tell")
            return
        
        # Check if replying to a message
        if message.reply_to_message:
            send_broadcast_message(message.reply_to_message)
        else:
            # Use the text after command
            announcement_msg = types.Message(
                message_id=message.message_id,
                from_user=message.from_user,
                date=message.date,
                chat=message.chat,
                content_type='text',
                options=[],
                json_string="",
                text=" ".join(args)
            )
            send_broadcast_message(announcement_msg)
        return

    if cmd == CMD_STATS:
        total_users = get_user_count()
        approved_users = len(get_approved_users())
        vip_users = len(get_vip_users())
        
        stats_text = (
            f"📊 <b>Bot Statistics</b>\n\n"
            f"👥 Total Users: {total_users}\n"
            f"✅ Approved Users: {approved_users}\n"
            f"⭐ VIP Users (All Access): {vip_users}\n"
            f"📚 Available Materials: {len(get_material_list())}"
        )
        bot.reply_to(message, stats_text)
        return

# --------------------------
# MAIN MESSAGE HANDLER
# --------------------------
@bot.message_handler(func=lambda m: True, content_types=[
    "text", "photo", "video", "document", "audio", "voice", "contact",
    "animation", "sticker", "location", "venue", "poll"
])
def handle_all_messages(message: Message):
    chat_id = message.chat.id
    from_user = message.from_user
    text = message.text.strip() if message.text else ""

    # Track new users
    if chat_id != ADMIN_CHAT_ID:
        add_user(from_user.id, from_user.username, from_user.first_name, from_user.last_name)

    # 1) Handle admin states
    if chat_id in admin_states:
        state = admin_states[chat_id]
        mode = state.get("mode")
        step = state.get("step")
        keyword = state.get("keyword")

        # ADDING FLOW
        if mode == "adding":
            if step == "awaiting_description":
                desc = text if text else (message.caption if getattr(message, "caption", None) else "")
                state["description"] = desc
                state["step"] = "awaiting_content"
                bot.reply_to(message, ("🚀 Now send your main content (text, photos, files, etc).\n"
                                       "You can send multiple messages.\n"
                                       "When finished, send /done\n\n"
                                       "💡 Want to add demo content? Send /demo_content after main content."))
                return

            elif step == "awaiting_content":
                if text and text.lower() == "/done":
                    # Save material and content
                    add_material_db(keyword, state.get("price"), state.get("description"))
                    collected = state.get("collected_saved_message_ids", [])
                    for idx, (saved_mid, content_type) in enumerate(collected, start=1):
                        add_content_entry_db(keyword, saved_mid, idx, content_type)
                    
                    # Send notification to all users about new material
                    new_product_text = (
                        f"🎉 <b>New Material Available!</b>\n\n"
                        f"📚 <b>{html.escape(keyword)}</b>\n"
                        f"💰 Price: {html.escape(state.get('price', ''))}\n"
                        f"📝 {html.escape(state.get('description', ''))}\n\n"
                        f"Use /product to see all materials!"
                    )
                    
                    users = get_all_users()
                    for user_id in users:
                        try:
                            send_long_text_split(user_id, new_product_text)
                            time.sleep(SHORT_DELAY)
                        except:
                            pass
                    
                    bot.reply_to(message, f"✅ Material <b>{html.escape(keyword)}</b> added with {len(collected)} content messages!\n📢 Notified {len(users)} users.")
                    reset_admin_state(chat_id)
                    return
                
                elif text and text.lower() == "/demo_content":
                    state["step"] = "awaiting_demo_content"
                    bot.reply_to(message, "🎬 Now send demo content (will be available via /demo command).\nSend /done when finished.")
                    return

                bot.reply_to(message, "🔄 Saving content to admin chat...")
                captured = capture_saved_message_id_from_admin_message(message)
                if captured:
                    saved_mid, content_type = captured
                    state.setdefault("collected_saved_message_ids", []).append((int(saved_mid), content_type))
                    bot.reply_to(message, f"✅ Content saved! (ID: {saved_mid})\nSend more content or /done when finished.")
                else:
                    bot.reply_to(message, "❌ Failed to save content. Try again.")
                return

            elif step == "awaiting_demo_content":
                if text and text.lower() == "/done":
                    collected_demo = state.get("collected_demo_message_ids", [])
                    start_index = state.get("demo_next_order_index", 1)
                    for idx, (saved_mid, content_type) in enumerate(collected_demo, start=start_index):
                        add_content_entry_db(keyword, saved_mid, idx, content_type, is_demo=True)
                    bot.reply_to(message, f"✅ Added {len(collected_demo)} demo content messages!\nNow send main content or /done to finish.")
                    state["step"] = "awaiting_content"
                    return

                bot.reply_to(message, "🔄 Saving demo content...")
                captured = capture_saved_message_id_from_admin_message(message)
                if captured:
                    saved_mid, content_type = captured
                    state.setdefault("collected_demo_message_ids", []).append((int(saved_mid), content_type))
                    bot.reply_to(message, f"✅ Demo content saved! (ID: {saved_mid})\nSend more demo content or /done when finished.")
                else:
                    bot.reply_to(message, "❌ Failed to save demo content. Try again.")
                return

        # UPDATING FLOW
        if mode == "updating":
            if step == "awaiting_update_choice":
                choice = text.strip().lower()
                if choice == "price":
                    state["step"] = "awaiting_new_price"
                    bot.reply_to(message, "💵 Send the new price.")
                    return
                if choice == "description":
                    state["step"] = "awaiting_new_description"
                    bot.reply_to(message, "📝 Send the new description.")
                    return
                if choice == "add_content":
                    state["step"] = "awaiting_content_to_add"
                    state["collected_saved_message_ids"] = []
                    bot.reply_to(message, "📦 Send new content to add.\nWhen finished send /done")
                    return
                if choice == "delete_content":
                    state["step"] = "awaiting_delete_content_id"
                    bot.reply_to(message, "🗑️ Send the message_id to delete, or send ALL to delete all content.")
                    return
                if choice == "add_demo":
                    state["step"] = "awaiting_demo_to_add"
                    state["collected_demo_message_ids"] = []
                    bot.reply_to(message, "🎬 Send new demo content to add.\nWhen finished send /done")
                    return
                if choice == "delete_demo":
                    state["step"] = "awaiting_delete_demo_id"
                    bot.reply_to(message, "🗑️ Send the demo message_id to delete, or send ALL to delete all demo content.")
                    return
                bot.reply_to(message, "❌ Unknown choice. Send one of: price / description / add_content / delete_content / add_demo / delete_demo")
                return

            if step == "awaiting_new_price":
                new_price = text.strip()
                if update_material_field_db(keyword, "price", new_price):
                    # Notify users about price change
                    price_update_text = f"💰 Price updated for <b>{html.escape(keyword)}</b>: {html.escape(new_price)}"
                    users = get_all_users()
                    for user_id in users:
                        try:
                            bot.send_message(user_id, price_update_text)
                            time.sleep(SHORT_DELAY)
                        except:
                            pass
                    bot.reply_to(message, f"✅ Price updated and notified {len(users)} users.")
                else:
                    bot.reply_to(message, "❌ Failed to update price.")
                reset_admin_state(chat_id)
                return

            if step == "awaiting_new_description":
                new_desc = text
                if update_material_field_db(keyword, "description", new_desc):
                    bot.reply_to(message, f"✅ Description updated for {html.escape(keyword)}.")
                else:
                    bot.reply_to(message, "❌ Failed to update description.")
                reset_admin_state(chat_id)
                return

            if step == "awaiting_content_to_add":
                if text and text.lower() == "/done":
                    collected = state.get("collected_saved_message_ids", [])
                    start_index = get_next_order_index(keyword)
                    for idx, (saved_mid, content_type) in enumerate(collected, start=start_index):
                        add_content_entry_db(keyword, saved_mid, idx, content_type)
                    bot.reply_to(message, f"✅ Added {len(collected)} new content messages to <b>{html.escape(keyword)}</b>.")
                    reset_admin_state(chat_id)
                    return
                
                captured = capture_saved_message_id_from_admin_message(message)
                if captured:
                    saved_mid, content_type = captured
                    state.setdefault("collected_saved_message_ids", []).append((int(saved_mid), content_type))
                    bot.reply_to(message, f"✅ Content saved! (ID: {saved_mid})\nSend more or /done")
                else:
                    bot.reply_to(message, "❌ Failed to save content.")
                return

            if step == "awaiting_demo_to_add":
                if text and text.lower() == "/done":
                    collected = state.get("collected_demo_message_ids", [])
                    start_index = get_next_order_index(keyword, is_demo=True)
                    for idx, (saved_mid, content_type) in enumerate(collected, start=start_index):
                        add_content_entry_db(keyword, saved_mid, idx, content_type, is_demo=True)
                    bot.reply_to(message, f"✅ Added {len(collected)} new demo messages to <b>{html.escape(keyword)}</b>.")
                    reset_admin_state(chat_id)
                    return
                
                captured = capture_saved_message_id_from_admin_message(message)
                if captured:
                    saved_mid, content_type = captured
                    state.setdefault("collected_demo_message_ids", []).append((int(saved_mid), content_type))
                    bot.reply_to(message, f"✅ Demo content saved! (ID: {saved_mid})\nSend more or /done")
                else:
                    bot.reply_to(message, "❌ Failed to save demo content.")
                return

            if step == "awaiting_delete_content_id":
                param = text.strip()
                if param.lower() == "all":
                    delete_content_entry_db(keyword)
                    bot.reply_to(message, f"🗑️ Deleted all content for <b>{html.escape(keyword)}</b>.")
                else:
                    try:
                        mid_to_delete = int(param)
                        delete_content_entry_db(keyword, mid_to_delete)
                        bot.reply_to(message, f"🗑️ Deleted message {mid_to_delete} from <b>{html.escape(keyword)}</b>.")
                    except:
                        bot.reply_to(message, "❌ Invalid message id.")
                reset_admin_state(chat_id)
                return

            if step == "awaiting_delete_demo_id":
                param = text.strip()
                if param.lower() == "all":
                    delete_content_entry_db(keyword, is_demo=True)
                    bot.reply_to(message, f"🗑️ Deleted all demo content for <b>{html.escape(keyword)}</b>.")
                else:
                    try:
                        mid_to_delete = int(param)
                        delete_content_entry_db(keyword, mid_to_delete, is_demo=True)
                        bot.reply_to(message, f"🗑️ Deleted demo message {mid_to_delete} from <b>{html.escape(keyword)}</b>.")
                    except:
                        bot.reply_to(message, "❌ Invalid message id.")
                reset_admin_state(chat_id)
                return

        # USER DEMO REQUEST
        if mode == "user_demo" and step == "awaiting_demo_keyword":
            send_demo_to_user(chat_id, text)
            reset_admin_state(chat_id)
            return

        # USER GET REQUEST
        if mode == "user_get" and step == "awaiting_get_keyword":
            send_material_to_user(chat_id, from_user.id, text)
            reset_admin_state(chat_id)
            return

    # 2) User keyword requests (direct text input)
    if text and not text.startswith("/"):
        keyword = text.strip().lower()
        mat = get_material(keyword)
        if not mat:
            bot.reply_to(message, "❌ Invalid keyword. Use /product to see available materials.")
            return
        
        if not user_is_approved_for(from_user.id, keyword):
            bot.reply_to(message, f"❌ You are not approved for <b>{html.escape(keyword)}</b>\nContact admin: @{ADMIN_USERNAME}")
            return
        
        send_material_to_user(chat_id, from_user.id, keyword)

# --------------------------
# RUN BOT
# --------------------------
def run_bot():
    logger.info("Starting Telebot polling.")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    print("🚀 Starting Full Selling Bot - SIMPLIFIED VERSION")
    print("📱 Running bot now...")
    run_bot()