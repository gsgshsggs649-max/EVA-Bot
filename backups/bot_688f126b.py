import telebot
import random
import time
import sqlite3
import os
import logging
from telebot.types import ReplyKeyboardMarkup
from telebot import types

# ===================== LOGGING =====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===================== CONFIG =====================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN متغير البيئة غير محدد")
    exit(1)

MAIN_ID = int(os.getenv("MAIN_ID", 5900695251))
DEV_ONLY_ID = int(os.getenv("DEV_ONLY_ID", MAIN_ID))

bot = telebot.TeleBot(TOKEN)

# ردود عشوائية لمجموعة المطور الخاص
RANDOM_REPLIES = [
    "أهلاً بك يا مطوري العزيز! 🤖",
    "كيف يمكنني مساعدتك اليوم؟",
    "نظام EVA يعمل بكفاءة تامة.",
    "أنا جاهز لأي أوامر إضافية."
]

# ===================== DATABASE =====================

def init_database():
    """تهيئة قاعدة البيانات"""
    try:
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

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS random_replies (
            word TEXT,
            reply TEXT
        )
        """)

        conn.commit()
        logger.info("✅ قاعدة البيانات تم تهيئتها بنجاح")
        return conn, cursor
    except sqlite3.Error as e:
        logger.error(f"❌ خطأ في قاعدة البيانات: {e}")
        raise

conn, cursor = init_database()

# ===================== SYSTEM =====================

def add_user(user):
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
        """, (user.id, user.username, user.first_name))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"❌ خطأ في إضافة المستخدم: {e}")

def get_balance(uid):
    try:
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        r = cursor.fetchone()
        return r[0] if r else 0
    except sqlite3.Error as e:
        logger.error(f"❌ خطأ في الحصول على الرصيد: {e}")
        return 0

def add_balance(uid, amount):
    try:
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"❌ خطأ في إضافة الرصيد: {e}")

def get_rank(uid):
    try:
        cursor.execute("SELECT rank FROM users WHERE user_id=?", (uid,))
        r = cursor.fetchone()
        return r[0] if r else "member"
    except sqlite3.Error as e:
        logger.error(f"❌ خطأ في الحصول على الرتبة: {e}")
        return "member"

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

# ===================== START (موحد للمجموعات والخاص) =====================

@bot.message_handler(commands=['start'])
def start(message):
    # سجّل المستخدم في القاعدة
    add_user(message.from_user)

    # خاصة
    if message.chat.type == "private":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton("الختمه"), types.KeyboardButton("اذكار"))

        # إضافة زر لوحة المطور إذا كان المرسل هو MAIN_ID
        if message.from_user.id == MAIN_ID:
            markup.row(types.KeyboardButton("⚙️ لوحة المطور"))

        bot.send_message(message.chat.id, "أهلاً بك في EVA Bot 🤖", reply_markup=markup)
        return

    # مجموعات / قنوات
    bot.reply_to(message, "🤖 EVA BOT جاهز", reply_markup=main_menu())

# ===================== بحث اغاني يوتيوب =====================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("اغنيه "))
def song_search(message):

    try:
        query = message.text.replace("اغنيه ", "")

        if not query:
            bot.reply_to(message, "❌ اكتب اسم الاغنية")
            return

        search = VideosSearch(query, limit=1)
        result = search.result()["result"][0]

        title = result["title"]
        link = result["link"]
        duration = result["duration"]
        channel = result["channel"]["name"]

        bot.reply_to(
            message,
            f"""🎵 نتيجة البحث

📌 الاسم: {title}

⏰ المدة: {duration}

📺 القناة: {channel}

🔗 الرابط:
{link}
"""
        )

    except Exception as e:
        logger.error(f"❌ خطأ في بحث الاغاني: {e}")
        bot.reply_to(message, "❌ ما حصلت الاغنية")

# ===================== DELEGATE HANDLERS TO handlers.py =====================
# سيتم استيراد handlers بعد تعريف المتغيرات الأساسية (bot, conn, cursor، الخ.)
try:
    import handlers  # noqa: F401
    logger.info("✅ handlers module loaded")
except Exception as e:
    logger.error(f"❌ خطأ في استيراد handlers: {e}")

# =========================================
# RUN BOT
# =========================================

if __name__ == "__main__":
    logger.info("🚀 EVA BOT يبدأ التشغيل...")
    try:
        bot.infinity_polling(skip_pending=True)
    except KeyboardInterrupt:
        logger.info("⏹️ البوت تم إيقافه")
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("✅ تم إغلاق قاعدة البيانات")
