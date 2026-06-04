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
    add_user(message.from_user)

    if message.chat.type == "private":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton("الختمه"), types.KeyboardButton("اذكار"))
        if message.from_user.id == MAIN_ID:
            markup.row(types.KeyboardButton("⚙️ لوحة المطور"))
        bot.send_message(message.chat.id, "أهلاً بك في EVA Bot 🤖", reply_markup=markup)
        return

    bot.reply_to(message, "🤖 EVA BOT جاهز", reply_markup=main_menu())

# ===================== MENUS (الأساسية) =====================

@bot.message_handler(func=lambda m: m.text == "🎮 الألعاب")
def games(message):
    bot.reply_to(message, "🎮 الألعاب", reply_markup=games_menu())

@bot.message_handler(func=lambda m: m.text == "📜 الأوامر")
def cmds(message):
    bot.reply_to(message, "📜 الأوامر", reply_markup=commands_menu())

@bot.message_handler(func=lambda m: m.text == "رجوع ⬅️")
def back(message):
    bot.reply_to(message, "⬅️ القائمة الرئيسية", reply_markup=main_menu())

# --- قائمة الأوامر (التي تظهر عند كتابة "الأوامر") ---
@bot.message_handler(func=lambda m: m.text == "الأوامر")
def send_main_menu(message):
    # متاحة في المجموعات فقط (group & supergroup)
    if message.chat.type not in ("group", "supergroup"):
        bot.reply_to(message, "❌ هذه الأوامر متاحة في المجموعات فقط.")
        return

    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("🛡 1", callback_data="cmd_admin"),
        types.InlineKeyboardButton("⚙ 2", callback_data="cmd_settings"),
        types.InlineKeyboardButton("🔧 3", callback_data="cmd_locks"),
        types.InlineKeyboardButton("📽 4", callback_data="cmd_media"),
        types.InlineKeyboardButton("🤖 5", callback_data="cmd_dev"),
        types.InlineKeyboardButton("✨ 8", callback_data="cmd_others")
    )
    markup.add(types.InlineKeyboardButton("القفل والفتح", callback_data="lock_unlock_menu"))
    markup.add(types.InlineKeyboardButton("التفعيل والتعطيل", callback_data="enable_disable_menu"))
    markup.add(types.InlineKeyboardButton("🔥 متجر روز الرقمي", url="https://t.me/your_store"))
    # زر الرجوع
    markup.add(types.InlineKeyboardButton("رجوع ⬅️", callback_data="back_main"))

    bot.reply_to(message, "📜 أهلاً بك عزيزي في قائمة الاوامر:", reply_markup=markup)

# --- قائمة الألعاب (التي تظهر عند كتابة "الالعاب") ---
@bot.message_handler(func=lambda m: m.text == "الالعاب")
def send_games_menu(message):
    # متاحة في المجموعات فقط (group & supergroup)
    if message.chat.type not in ("group", "supergroup"):
        bot.reply_to(message, "❌ هذه الأوامر متاحة في المجموعات فقط.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("لعبة النواجي", callback_data="game_nawadi"),
        types.InlineKeyboardButton("لعبة الغزاه", callback_data="game_ghzah"),
        types.InlineKeyboardButton("لعبة البنك", callback_data="game_bank"),
        types.InlineKeyboardButton("العاب اونلاين", callback_data="game_online")
    )
    # زر الرجوع
    markup.add(types.InlineKeyboardButton("رجوع ⬅️", callback_data="back_games"))

    bot.reply_to(message, "🎮 اختر لعبة للبدء:", reply_markup=markup)

# ===================== ECONOMY =====================

@bot.message_handler(func=lambda m: m.text == "💰 فلوسي")
def money(message):
    bot.reply_to(message, f"💰 {get_balance(message.from_user.id)}")

@bot.message_handler(func=lambda m: m.text == "💵 راتب")
def salary(message):
    add_balance(message.from_user.id, 100)
    bot.reply_to(message, "💵 +100")

# -- تحويل عبر الرد أو ذكر المستخدم أو باستخدام الفواصل |
@bot.message_handler(func=lambda m: m.text and m.text.startswith("تحويل"))
def transfer(message):
    try:
        sender = message.from_user
        add_user(sender)

        # حالة: الرد على رسالة المستخدم، الصيغة: "تحويل 100" كرد
        if message.reply_to_message:
            try:
                parts = message.text.split()
                if len(parts) < 2:
                    bot.reply_to(message, "❌ اكتب: تحويل <المبلغ> كرد على رسالة المستخدم")
                    return
                amount = int(parts[1])
            except Exception:
                bot.reply_to(message, "❌ المبلغ يجب أن يكون رقماً صحيحاً")
                return
            receiver = message.reply_to_message.from_user
            add_user(receiver)

        else:
            # حالة: تحويل | @user | المبلغ أو تحويل @user المبلغ
            if "|" in message.text:
                parts = message.text.split("|")
                if len(parts) < 3:
                    bot.reply_to(message, "❌ الصيغة: تحويل | @user | المبلغ")
                    return
                username = parts[1].strip().replace("@", "")
                try:
                    amount = int(parts[2].strip())
                except Exception:
                    bot.reply_to(message, "❌ المبلغ يجب أن يكون رقماً صحيحاً")
                    return
            else:
                parts = message.text.split()
                if len(parts) < 3:
                    bot.reply_to(message, "❌ الصيغة: تحويل @user المبلغ أو رد على رسالة المستخدم بكتابة: تحويل المبلغ")
                    return
                username = parts[1].strip().replace("@", "")
                try:
                    amount = int(parts[2].strip())
                except Exception:
                    bot.reply_to(message, "❌ المبلغ يجب أن يكون رقماً صحيحاً")
                    return

            # البحث عن المستخدم في قاعدة البيانات
            cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
            r = cursor.fetchone()
            if not r:
                bot.reply_to(message, "❌ لم أجد المستخدم في السجل. استخدم الرد على رسالة المستخدم أو تأكد أنه تفاعل مع البوت من قبل.")
                return
            receiver_id = r[0]
            # إحضار بيانات المستخدم الباقية إن أمكن
            receiver = types.User(id=receiver_id, first_name=username, username=username) if False else None

            # إذا لم نحصل على كائن receiver (غير متوفر)، سنستخدم receiver_id لاحقًا

        # تحقق من صحة المبلغ
        if amount <= 0:
            bot.reply_to(message, "❌ المبلغ يجب أن يكون أكبر من صفر")
            return

        sender_balance = get_balance(sender.id)
        if sender_balance < amount:
            bot.reply_to(message, "❌ رصيدك غير كافٍ للتحويل")
            return

        # تنفيذ التحويل
        add_balance(sender.id, -amount)
        if message.reply_to_message:
            add_balance(receiver.id, amount)
            bot.reply_to(message, f"✅ تم تحويل {amount} إلى {receiver.first_name}\nرصيدك الآن: {get_balance(sender.id)}")
        else:
            add_balance(receiver_id, amount)
            bot.reply_to(message, f"✅ تم تحويل {amount} إلى @{username}\nرصيدك الآن: {get_balance(sender.id)}")

    except Exception as e:
        logger.error(f"❌ خطأ في عملية التحويل: {e}")
        bot.reply_to(message, "❌ حدث خطأ أثناء تنفيذ التحويل. حاول لاحقًا.")

# ===================== GAMES (رسائل سريعة) =====================

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
        try:
            bot.send_message(receiver, "📩 عندك همسة جديدة اكتب (همساتي)")
        except Exception:
            pass
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
        cursor.execute("INSERT INTO replies VALUES (?,?)", (word, reply))
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
                cursor.execute("INSERT INTO replies VALUES (?,?)", (word, reply_text))
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

# =========================================
# CALLBACK BUTTONS (م��حد - يشمل أوامر الألعاب والأوامر والإعدادات)
# =========================================

@bot.callback_query_handler(func=lambda call: True)
def callback_buttons(call):
    # منع استخدام هذه الأزرار في الخاص
    if not call.message or not call.message.chat or call.message.chat.type not in ("group", "supergroup"):
        try:
            bot.answer_callback_query(call.id, "❌ هذه الأوامر متاحة في المجموعات فقط.")
        except Exception:
            pass
        return

    # زر الرجوع من قوائم الأوامر (يعيد عرض نفس قائمة الأوامر)
    if call.data == "back_main":
        try:
            markup = types.InlineKeyboardMarkup(row_width=3)
            markup.add(
                types.InlineKeyboardButton("🛡 1", callback_data="cmd_admin"),
                types.InlineKeyboardButton("⚙ 2", callback_data="cmd_settings"),
                types.InlineKeyboardButton("🔧 3", callback_data="cmd_locks"),
                types.InlineKeyboardButton("📽 4", callback_data="cmd_media"),
                types.InlineKeyboardButton("🤖 5", callback_data="cmd_dev"),
                types.InlineKeyboardButton("✨ 8", callback_data="cmd_others")
            )
            markup.add(types.InlineKeyboardButton("القفل والفتح", callback_data="lock_unlock_menu"))
            markup.add(types.InlineKeyboardButton("التفعيل والتعطيل", callback_data="enable_disable_menu"))
            markup.add(types.InlineKeyboardButton("🔥 متجر روز الرقمي", url="https://t.me/your_store"))
            markup.add(types.InlineKeyboardButton("رجوع ⬅️", callback_data="back_main"))

            bot.answer_callback_query(call.id)
            bot.edit_message_text("📜 أهلاً بك عزيزي في قائمة الاوامر:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة back_main: {e}")
        return

    # زر الرجوع من قائمة الألعاب (يعيد عرض نفس قائمة الألعاب)
    if call.data == "back_games":
        try:
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("لعبة النواجي", callback_data="game_nawadi"),
                types.InlineKeyboardButton("لعبة الغزاه", callback_data="game_ghzah"),
                types.InlineKeyboardButton("لعبة البنك", callback_data="game_bank"),
                types.InlineKeyboardButton("العاب اونلاين", callback_data="game_online")
            )
            markup.add(types.InlineKeyboardButton("رجوع ⬅️", callback_data="back_games"))

            bot.answer_callback_query(call.id)
            bot.edit_message_text("🎮 اختر لعبة للبدء:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة back_games: {e}")
        return

    # تعامل مع أوامر القائمة (cmd_) — مثال للختمة/اذكار/قرآن
    if call.data.startswith("cmd_"):
        if call.data == "cmd_khatma":
            try:
                bot.answer_callback_query(call.id, "جاري فتح الختمة...")
                bot.send_message(call.message.chat.id, "📖 تم فتح الختمة — استمتع بالقراءة! (أضف منطق الختمة هنا)")
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الختمة: {e}")
            return
        elif call.data == "cmd_azkar":
            try:
                bot.answer_callback_query(call.id, "جاري عرض الأذكار...")
                bot.send_message(call.message.chat.id, "🕌 أذكار: سبحان الله، الحمد لله، الله أكبر ...")
            except Exception as e:
                logger.error(f"❌ خطأ في عرض الأذكار: {e}")
            return
        elif call.data == "cmd_quran":
            try:
                bot.answer_callback_query(call.id, "جاري فتح القرآن...")
                bot.send_message(call.message.chat.id, "📚 القرآن: يمكنك إرسال /quran أو رابط لسورة محددة (ميزة قيد الإعداد).")
            except Exception as e:
                logger.error(f"❌ خطأ في فتح القرآن: {e}")
            return

    # تعامل مع الألعاب (game_)
    if call.data.startswith("game_"):
        try:
            if call.data in ("game_nawadi", "game_luck"):
                bot.edit_message_text(f"🍀 حظك اليوم: {random.randint(1,100)}%", call.message.chat.id, call.message.message_id)
            elif call.data in ("game_ghzah", "game_spin"):
                bot.edit_message_text(f"🎲 النتيجة: {random.choice(['ربحت 🎉','خسرت 💔','جائزة 👑'])}", call.message.chat.id, call.message.message_id)
            elif call.data == "game_bank":
                bot.edit_message_text("🏦 لعبة البنك: قيد الإعداد.", call.message.chat.id, call.message.message_id)
            elif call.data == "game_online":
                bot.edit_message_text("🔗 العاب اونلاين: افتح الرابط للعب.", call.message.chat.id, call.message.message_id)
        except Exception as e:
            logger.error(f"❌ خطأ في منطق الألعاب: {e}")
        return

    # اوامر الادمن / الاعدادات السابقة (لضمان التوافق)
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
        back = types.InlineKeyboardButton("رجوع", callback_data="back_main")
        markup.add(back)
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception as e:
            logger.error(f"❌ خطأ في admin_cmds callback: {e}")
        return

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
            b1 = types.InlineKeyboardButton(name, callback_data="none")
            b2 = types.InlineKeyboardButton(state, callback_data="none")
            markup.add(b2, b1)
        back = types.InlineKeyboardButton("رجوع", callback_data="back_main")
        markup.add(back)
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception as e:
            logger.error(f"❌ خطأ في settings_cmds callback: {e}")
        return

    # بقية أزرار callback... (تبقى كما هي)

# =========================================
# PRIVATE REPLIES
# =========================================

@bot.message_handler(func=lambda m: m.text == "اذكار")
def azkar(message):
    bot.reply_to(message, "رضيت بالله رباً وبالاسلام ديناً وبمحمد ﷺ نبياً")

@bot.message_handler(func=lambda m: m.text == "اقتباسات")
def quotes(message):
    data = ["لا تيأس مهما حدث", "النجاح يبدأ بخطوة", "اصنع يومك بنفسك"]
    bot.reply_to(message, random.choice(data))

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
