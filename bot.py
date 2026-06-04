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
# معرف المطور الإضافي (يمكن ضبطه في المتغيرات البيئية أو يساوي MAIN_ID)
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
    bot.reply_to(message, f"🍀 {random.randint(1, 100)}%")

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
        
        if len(parts) < 3:
            bot.reply_to(message, "❌ الصيغة الصحيحة: همسه | @user | الرسالة")
            return

        msg = parts[2].strip()
        
        if not msg:
            bot.reply_to(message, "❌ الرسالة لا يمكن أن تكون فارغة")
            return

        if message.reply_to_message:
            receiver = message.reply_to_message.from_user.id
        else:
            username = parts[1].strip().replace("@", "")
            
            if not username:
                bot.reply_to(message, "❌ اسم المستخدم لا يمكن أن يكون فارغاً")
                return
            
            cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
            r = cursor.fetchone()
            if not r:
                bot.reply_to(message, "❌ الشخص غير موجود")
                return
            receiver = r[0]

        cursor.execute("""
            INSERT INTO whispers (sender, receiver, chat_id, msg)
            VALUES (?,?,?,?)
        """, (message.from_user.id, receiver, message.chat.id, msg))

        conn.commit()

        bot.reply_to(message, "🤫 تم إرسال الهمسة")
        bot.send_message(receiver, "📩 عندك همسة جديدة اكتب (همساتي)")
        logger.info(f"✅ همسة من {message.from_user.id} إلى {receiver}")

    except ValueError as e:
        logger.error(f"❌ خطأ في معالجة الهمسة: {e}")
        bot.reply_to(message, "❌ الصيغة الصحيحة: همسه | @user | الرسالة")
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع في الهمسة: {e}")
        bot.reply_to(message, "❌ حدث خطأ، يرجى المحاولة لاحقاً")

@bot.message_handler(func=lambda m: m.text == "همساتي")
def my_whispers(message):
    try:
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
    except sqlite3.Error as e:
        logger.error(f"❌ خطأ في قراءة الهمسات: {e}")
        bot.reply_to(message, "❌ حدث خطأ، يرجى المحاولة لاحقاً")

# ===================== AUTO REPLY =====================

@bot.message_handler(func=lambda m: m.text and not m.text.startswith(("/", "اضف", "همس")))
def auto_reply(message):
    try:
        cursor.execute("SELECT reply FROM replies WHERE word=?", (message.text,))
        rows = cursor.fetchall()

        if rows:
            bot.reply_to(message, random.choice(rows)[0])
    except Exception as e:
        logger.error(f"❌ خطأ في الرد التلقائي: {e}")

# ===================== ADD SINGLE REPLY =====================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("اضف رد |"))
def add_reply(message):
    if message.from_user.id != MAIN_ID:
        bot.reply_to(message, "❌ ليس لديك صلاحية")
        return

    try:
        parts = message.text.split("|")
        
        if len(parts) < 3:
            bot.reply_to(message, "❌ الصيغة الصحيحة: اضف رد | الكلمة | الرد")
            return

        word = parts[1].strip()
        reply = parts[2].strip()
        
        if not word or not reply:
            bot.reply_to(message, "❌ الكلمة والرد لا يمكن أن تكونا فارغتين")
            return

        cursor.execute(
            "INSERT INTO replies VALUES (?,?)",
            (word, reply)
        )

        conn.commit()

        bot.reply_to(message, "✅ تمت إضافة الرد")
        logger.info(f"✅ تم إضافة رد جديد: {word}")

    except Exception as e:
        logger.error(f"❌ خطأ في إضافة الرد: {e}")
        bot.reply_to(message, "❌ الصيغة الصحيحة: اضف رد | الكلمة | الرد")

# ===================== ADD MULTI REPLIES =====================

@bot.message_handler(func=lambda m: m.text and m.text.startswith("اضف ردود متعددة"))
def add_multi_reply(message):
    if message.from_user.id != MAIN_ID:
        bot.reply_to(message, "❌ ليس لديك صلاحية")
        return

    try:
        parts = message.text.split("|")
        
        if len(parts) < 3:
            bot.reply_to(message, "❌ الصيغة الصحيحة: اضف ردود متعددة | الكلمة | رد1,رد2,رد3")
            return

        word = parts[1].strip()
        replies = parts[2].strip()
        
        if not word or not replies:
            bot.reply_to(message, "❌ الكلمة والردود لا يمكن أن تكون فارغة")
            return

        for r in replies.split(","):
            reply_text = r.strip()
            if reply_text:
                cursor.execute(
                    "INSERT INTO replies VALUES (?,?)",
                    (word, reply_text)
                )

        conn.commit()

        bot.reply_to(message, "✅ تمت إضافة الردود المتعددة")
        logger.info(f"✅ تم إضافة ردود متعددة للكلمة: {word}")

    except Exception as e:
        logger.error(f"❌ خطأ في إضافة الردود المتعددة: {e}")
        bot.reply_to(message, "❌ الصيغة الصحيحة: اضف ردود متعددة | الكلمة | رد1,رد2,رد3")

# ===================== LIST REPLIES =====================

@bot.message_handler(func=lambda m: m.text == "قائمه الردود")
def list_replies(message):
    if message.from_user.id != MAIN_ID:
        bot.reply_to(message, "❌ ليس لديك صلاحية")
        return

    try:
        cursor.execute("SELECT word, reply FROM replies")

        rows = cursor.fetchall()

        if not rows:
            bot.reply_to(message, "❌ لا توجد ردود")
            return

        text = "📜 قائمة الردود:\n\n"

        for r in rows:
            text += f"• {r[0]} ← {r[1]}\n"

        bot.reply_to(message, text)
    except Exception as e:
        logger.error(f"❌ خطأ في عرض الردود: {e}")
        bot.reply_to(message, "❌ حدث خطأ، يرجى المحاولة لاحقاً")

# ===================== ID =====================

@bot.message_handler(func=lambda m: m.text == "ايدي")
def myid(message):
    try:
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
    except Exception as e:
        logger.error(f"❌ خطأ في عرض بيانات المستخدم: {e}")
        bot.reply_to(message, "❌ حدث خطأ، يرجى المحاولة لاحقاً")

# ===================== SAVE USERS (معالجة عامة) =====================

@bot.message_handler(func=lambda m: True)
def save_user(message):
    # تحفظ المستخدم وتوجه الرسالة إلى معالج الرسائل الرئيسي
    try:
        user_id = message.from_user.id

        cursor.execute(
            "SELECT * FROM users WHERE user_id=?",
            (user_id,)
        )

        data = cursor.fetchone()

        if not data:
            cursor.execute(
                "INSERT INTO users (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()

        # تمرير للمعالجة الرئيسية (تتعامل مع الاوامر والردود العشوائية)
        process_messages(message)
    except Exception as e:
        logger.error(f"❌ خطأ في save_user: {e}")

# =========================================
# MAIN PROCESS
# =========================================

def process_messages(message):

    text = message.text or ""

    # =====================================
    # الاوامر
    # =====================================

    if text in ["الاوامر", "/commands"]:

        msg = """
• أهلاً بك عزيزي في قائمة الاوامر :

⌔ 1 : اوامر الادمنيه
⌔ 2 : اوامر الاعدادات
⌔ 3 : اوامر القفل - الفتح
⌔ 4 : اوامر التسلية
⌔ 5 : اوامر Dev
⌔ 6 : الاوامر الخدمية
"""

        markup = types.InlineKeyboardMarkup(row_width=3)

        b1 = types.InlineKeyboardButton("🛡 1", callback_data="admin_cmds")
        b2 = types.InlineKeyboardButton("⚙ 2", callback_data="settings_cmds")
        b3 = types.InlineKeyboardButton("🔧 3", callback_data="lock_cmds")

        b4 = types.InlineKeyboardButton("🎮 4", callback_data="games_cmds")
        b5 = types.InlineKeyboardButton("🤖 5", callback_data="dev_cmds")
        b6 = types.InlineKeyboardButton("✨ 6", callback_data="service_cmds")

        b7 = types.InlineKeyboardButton("القفل والفتح", callback_data="lock_menu")
        b8 = types.InlineKeyboardButton("التفعيل والتعطيل", callback_data="enable_disable")

        markup.add(b1, b2, b3)
        markup.add(b4, b5, b6)
        markup.add(b7, b8)

        bot.reply_to(message, msg, reply_markup=markup)
        return

    # =====================================
    # لوحة المطور السرية
    # =====================================

    if text == "لوحة المطور":

        if message.from_user.id != DEV_ONLY_ID:
            return

        msg = """
🔒 لوحة المطور السرية

• الردود العشوائية
• الردود المتعددة
• اذاعة
• نسخة احتياطية
• تنظيف الردود
• الاحصائيات
"""

        markup = types.InlineKeyboardMarkup(row_width=2)

        b1 = types.InlineKeyboardButton("الردود", callback_data="random_replies")
        b2 = types.InlineKeyboardButton("الاحصائيات", callback_data="stats")

        b3 = types.InlineKeyboardButton("تنظيف", callback_data="clean")
        b4 = types.InlineKeyboardButton("اذاعة", callback_data="broadcast")

        markup.add(b1, b2)
        markup.add(b3, b4)

        bot.reply_to(message, msg, reply_markup=markup)
        return

    # =====================================
    # اضافة رد عشوائي
    # =====================================

    if text.startswith("اضف رد عشوائي"):

        if message.from_user.id != DEV_ONLY_ID:
            return

        try:

            data = text.split("|")

            word = data[1].strip()
            reply = data[2].strip()

            cursor.execute(
                "INSERT INTO random_replies VALUES (?,?)",
                (word, reply)
            )

            conn.commit()

            bot.reply_to(
                message,
                f"✓ تم اضافة رد عشوائي لـ : {word}"
            )

        except Exception:
            bot.reply_to(
                message,
                "الصيغة:\nاضف رد عشوائي | الكلمة | الرد"
            )
        return

    # =====================================
    # حذف الرد العشوائي
    # =====================================

    if text.startswith("حذف الرد العشوائي"):

        if message.from_user.id != DEV_ONLY_ID:
            return

        try:

            word = text.split("|")[1].strip()

            cursor.execute(
                "DELETE FROM random_replies WHERE word=?",
                (word,)
            )

            conn.commit()

            bot.reply_to(
                message,
                f"✓ تم حذف الردود الخاصة بـ : {word}"
            )

        except Exception:
            bot.reply_to(
                message,
                "الصيغة:\nحذف الرد العشوائي | الكلمة"
            )
        return

    # =====================================
    # عرض الردود
    # =====================================

    if text == "الردود العشوائية":

        if message.from_user.id != DEV_ONLY_ID:
            return

        cursor.execute(
            "SELECT DISTINCT word FROM random_replies"
        )

        data = cursor.fetchall()

        if not data:
            bot.reply_to(message, "لا يوجد ردود")
            return

        msg = "• الردود العشوائية\n\n"

        for x in data:
            msg += f"⌔ {x[0]}\n"

        bot.reply_to(message, msg)
        return

    # =====================================
    # الاحصائيات
    # =====================================

    if text == "الاحصائيات":

        if message.from_user.id != DEV_ONLY_ID:
            return

        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM random_replies"
        )

        replies_count = cursor.fetchone()[0]

        msg = f"""
📊 احصائيات البوت

• عدد المستخدمين : {users_count}
• عدد الردود : {replies_count}
"""

        bot.reply_to(message, msg)
        return

    # =====================================
    # تنظيف الردود
    # =====================================

    if text == "تنظيف الردود":

        if message.from_user.id != DEV_ONLY_ID:
            return

        cursor.execute("DELETE FROM random_replies")
        conn.commit()

        bot.reply_to(
            message,
            "✓ تم حذف جميع الردود"
        )
        return

    # =====================================
    # اذاعة
    # =====================================

    if text.startswith("اذاعة "):

        if message.from_user.id != DEV_ONLY_ID:
            return

        msg = text.replace("اذاعة ", "")

        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

        sent = 0

        for user in users:

            try:
                bot.send_message(user[0], msg)
                sent += 1
            except Exception:
                pass

        bot.reply_to(
            message,
            f"✓ تمت الاذاعة الى {sent}"
        )
        return

    # =====================================
    # الردود التلقائية العشوائية
    # =====================================

    cursor.execute(
        "SELECT reply FROM random_replies WHERE word=?",
        (text,)
    )

    replies = cursor.fetchall()

    if replies:

        random_reply = random.choice(replies)[0]

        bot.reply_to(
            message,
            random_reply
        )

# =========================================
# CALLBACK BUTTONS
# =========================================

@bot.callback_query_handler(func=lambda call: True)
def callback_buttons(call):

    # =====================================
    # اوامر الادمن
    # =====================================

    if call.data == "admin_cmds":

        text = """
• قائمة الاوامر الادمنية :

⌔ رفع ادمن
⌔ تنزيل ادمن
⌔ رفع مدير
⌔ تنزيل مدير
⌔ حظر
⌔ الغاء الحظر
⌔ كتم
⌔ الغاء الكتم
⌔ تثبيت
⌔ مسح
"""

        markup = types.InlineKeyboardMarkup()

        back = types.InlineKeyboardButton(
            "رجوع",
            callback_data="back_main"
        )

        markup.add(back)

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        return

    # =====================================
    # اوامر الاعدادات
    # =====================================

    elif call.data == "settings_cmds":

        text = """
• اعدادات المجموعة

• نعم = مقفول
• لا = مفتوح
"""

        markup = types.InlineKeyboardMarkup(row_width=2)

        settings = [
            ("الروابط ↞", "لا"),
            ("الكلايش ↞", "نعم"),
            ("الكيبورد ↞", "نعم"),
            ("الاغاني ↞", "لا"),
            ("المتحركة ↞", "لا"),
            ("الملفات ↞", "نعم"),
            ("الدردشة ↞", "لا"),
            ("الفيديو ↞", "لا"),
            ("الصور ↞", "لا"),
            ("المعرفات ↞", "نعم")
        ]

        for name, state in settings:

            b1 = types.InlineKeyboardButton(
                name,
                callback_data="none"
            )

            b2 = types.InlineKeyboardButton(
                state,
                callback_data="none"
            )

            markup.add(b2, b1)

        back = types.InlineKeyboardButton(
            "رجوع",
            callback_data="back_main"
        )

        markup.add(back)

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        return

    # بقية أزرار callback... (لا تغيير)

# =========================================
# PRIVATE REPLIES
# =========================================

@bot.message_handler(func=lambda m: m.text == "اذكار")
def azkar(message):

    bot.reply_to(
        message,
        "رضيت بالله رباً وبالاسلام ديناً وبمحمد ﷺ نبياً"
    )

@bot.message_handler(func=lambda m: m.text == "اقتباسات")
def quotes(message):

    data = [
        "لا تيأس مهما حدث",
        "النجاح يبدأ بخطوة",
        "اصنع يومك بنفسك"
    ]

    bot.reply_to(
        message,
        random.choice(data)
    )

# زر لوحة المطور في الخاص
@bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "⚙️ لوحة المطور")
def private_dev_panel(message):
    if message.from_user.id != MAIN_ID:
        return

    response = random.choice(RANDOM_REPLIES)
    bot.reply_to(message, f"مرحباً مطوري، {response}")

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
