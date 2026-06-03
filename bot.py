import telebot
import random
import time
import sqlite3
import os
from telebot.types import ReplyKeyboardMarkup

# ===================== CONFIG =====================

TOKEN = os.getenv("AAED9A0I-CQmxvOkPndQRbApG-oU_fByQlc")
MAIN_ID = 5900695251

bot = telebot.TeleBot(TOKEN)

# ===================== DATABASE =====================

conn = sqlite3.connect("eva.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    balance INTEGER DEFAULT 0,
    rank TEXT DEFAULT 'member'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS replies (
    word TEXT,
    reply TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS whispers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender INTEGER,
    receiver INTEGER,
    chat_id INTEGER,
    msg TEXT,
    seen INTEGER DEFAULT 0
)
""")

conn.commit()

# ===================== SYSTEM =====================

def add_user(user):
    cursor.execute("""
    INSERT OR IGNORE INTO users (user_id, username, first_name)
    VALUES (?, ?, ?)
    """, (user.id, user.username, user.first_name))
    conn.commit()

def get_balance(uid):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    r = cursor.fetchone()
    return r[0] if r else 0

def add_balance(uid, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    conn.commit()

def get_rank(uid):
    cursor.execute("SELECT rank FROM users WHERE user_id=?", (uid,))
    r = cursor.fetchone()
    return r[0] if r else "member"

# ===================== BUTTONS =====================

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💰 فلوسي", "💵 راتب")
    kb.row("🎮 الألعاب", "📜 الأوامر")
    kb.row("🤫 همساتي", "👑 رتبتي")
    return kb

def games_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("كت", "حظ", "لف")
    kb.row("صراحه", "لو خيروك")
    kb.row("رجوع ⬅️")
    return kb

def commands_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("فلوسي", "راتب")
    kb.row("تحويل", "هدية")
    kb.row("رجوع ⬅️")
    return kb

# ===================== START =====================

@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user)
    bot.reply_to(message, "🤖 EVA BOT جاهز", reply_markup=main_menu())

# ===================== MENUS =====================

@bot.message_handler(func=lambda m: m.text == "🎮 الألعاب")
def games(message):
    bot.reply_to(message, "🎮 الألعاب", reply_markup=games_menu())

@bot.message_handler(func=lambda m: m.text == "📜 الأوامر")
def cmds(message):
    bot.reply_to(message, "📜 الأوامر", reply_markup=commands_menu())

@bot.message_handler(func=lambda m: m.text == "رجوع ⬅️")
def back(message):
    bot.reply_to(message, "⬅️ القائمة الرئيسية", reply_markup=main_menu())

# ===================== ECONOMY =====================

@bot.message_handler(func=lambda m: m.text == "💰 فلوسي")
def money(message):
    bot.reply_to(message, f"💰 {get_balance(message.from_user.id)}")

@bot.message_handler(func=lambda m: m.text == "💵 راتب")
def salary(message):
    add_balance(message.from_user.id, 100)
    bot.reply_to(message, "💵 +100")

# ===================== GAMES =====================

@bot.message_handler(func=lambda m: m.text == "حظ")
def luck(message):
    bot.reply_to(message, f"🍀 {random.randint(1,100)}%")

@bot.message_handler(func=lambda m: m.text == "لف")
def spin(message):
    bot.reply_to(message, random.choice(["ربحت 🎉", "خسرت 💔", "جائزة 👑"]))

@bot.message_handler(func=lambda m: m.text == "كت")
def kt(message):
    bot.reply_to(message, random.choice([
        "هل أنت صريح؟",
        "هل تثق بالناس؟",
        "ما أكبر سر عندك؟"
    ]))

@bot.message_handler(func=lambda m: m.text == "صراحه")
def saraha(message):
    bot.reply_to(message, random.choice([
        "مين تحب؟",
        "مين تكره؟",
        "هل كذبت اليوم؟"
    ]))

@bot.message_handler(func=lambda m: m.text == "لو خيروك")
def would(message):
    bot.reply_to(message, random.choice([
        "حب أو مال؟",
        "نوم أو أكل؟",
        "سفر أو فلوس؟"
    ]))

# ===================== RANK =====================

@bot.message_handler(func=lambda m: m.text == "👑 رتبتي")
def rank(message):
    bot.reply_to(message, f"👑 {get_rank(message.from_user.id)}")

# ===================== WHISPERS =====================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("همسه"))
def whisper(message):

    try:
        parts = message.text.split("|")
        msg = parts[2]

        if message.reply_to_message:
            receiver = message.reply_to_message.from_user.id
        else:
            username = parts[1].replace("@", "")
            cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
            r = cursor.fetchone()
            if not r:
                bot.reply_to(message, "الشخص غير موجود")
                return
            receiver = r[0]

        cursor.execute("""
            INSERT INTO whispers (sender, receiver, chat_id, msg)
            VALUES (?,?,?,?)
        """, (message.from_user.id, receiver, message.chat.id, msg))

        conn.commit()

        bot.reply_to(message, "🤫 تم إرسال الهمسة")

        bot.send_message(receiver, "📩 عندك همسة جديدة اكتب (همساتي)")

    except:
        bot.reply_to(message, "همسه | @user | الرسالة")

@bot.message_handler(func=lambda m: m.text == "همساتي")
def my_whispers(message):

    cursor.execute("""
        SELECT sender, msg FROM whispers
        WHERE receiver=? AND seen=0
    """, (message.from_user.id,))

    rows = cursor.fetchall()

    if not rows:
        bot.reply_to(message, "📭 ما عندك همسات")
        return

    text = "📩 همساتك:\n\n"

    for r in rows:
        text += f"👤 {r[0]}: {r[1]}\n"

    cursor.execute("""
        UPDATE whispers SET seen=1 WHERE receiver=?
    """, (message.from_user.id,))

    conn.commit()

    bot.reply_to(message, text)

# ===================== AUTO REPLY =====================

@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def auto_reply(message):

    cursor.execute("SELECT reply FROM replies WHERE word=?", (message.text,))
    rows = cursor.fetchall()

    if rows:
        bot.reply_to(message, 
random.choice(rows)[0])
# ===================== ADD SINGLE REPLY =====================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("اضف رد |"))
def add_reply(message):

    if message.from_user.id != MAIN_ID:
        return

    try:

        _, word, reply = message.text.split("|")

        cursor.execute(
            "INSERT INTO replies VALUES (?,?)",
            (word.strip(), reply.strip())
        )

        conn.commit()

        bot.reply_to(message, "✅ تمت إضافة الرد")

    except:

        bot.reply_to(
            message,
            "اضف رد | الكلمة | الرد"
        )

# ===================== ADD MULTI REPLIES =====================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("اضف ردود متعددة"))
def add_multi_reply(message):

    if message.from_user.id != MAIN_ID:
        return

    try:

        _, word, replies = message.text.split("|")

        for r in replies.split(","):

            cursor.execute(
                "INSERT INTO replies VALUES (?,?)",
                (word.strip(), r.strip())
            )

        conn.commit()

        bot.reply_to(message, "✅ تمت إضافة الردود المتعددة")

    except:

        bot.reply_to(
            message,
            "اضف ردود متعددة | الكلمة | رد1,رد2,رد3"
        )

# ===================== LIST REPLIES =====================

@bot.message_handler(func=lambda m: m.text == "قائمه الردود")
def list_replies(message):

    if message.from_user.id != MAIN_ID:
        return

    cursor.execute("SELECT word, reply FROM replies")

    rows = cursor.fetchall()

    if not rows:

        bot.reply_to(message, "❌ لا توجد ردود")
        return

    text = "📜 قائمة الردود:\n\n"

    for r in rows:

        text += f"• {r[0]} ← {r[1]}\n"

    bot.reply_to(message, text)

# ===================== ID =====================

@bot.message_handler(func=lambda m: m.text == "ايدي")
def myid(message):

    user = message.from_user

    text = f"""
🆔 ايديك: {user.id}
👤 اسمك: {user.first_name}
📛 يوزرك: @{user.username if user.username else 'لا يوجد'}
"""

    photos = bot.get_user_profile_photos(user.id)

    if photos.total_count > 0:

        file_id = photos.photos[0][-1].file_id

        bot.send_photo(
            message.chat.id,
            file_id,
            caption=text
        )

    else:

        bot.reply_to(message, text)

# ===================== RUN =====================

print("EVA BOT FINAL CLEAN RUNNING 🔥")
bot.infinity_polling(skip_pending=True)
