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
conn = sqlite3.connect("eva.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, balance INTEGER DEFAULT 0, rank TEXT DEFAULT 'member')""")
cursor.execute("""CREATE TABLE IF NOT EXISTS replies (word TEXT, reply TEXT, type TEXT DEFAULT 'single', image TEXT DEFAULT NULL)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS whispers (id INTEGER PRIMARY KEY AUTOINCREMENT, sender INTEGER, receiver INTEGER, chat_id INTEGER, msg TEXT, seen INTEGER DEFAULT 0)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS random_replies (word TEXT, reply TEXT)""")
conn.commit()

# ===================== FUNCTIONS =====================
def add_user(user):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)", (user.id, user.username, user.first_name))
    conn.commit()

def get_balance(uid):
    cursor.execute("SELECT balance FROM users WHERE user_id= ?", (uid,))
    r = cursor.fetchone()
    return r[0] if r else 0

def add_balance(uid, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    conn.commit()

def get_rank(uid):
    cursor.execute("SELECT rank FROM users WHERE user_id=?", (uid,))
    r = cursor.fetchone()
    return r[0] if r else "member"

# ===================== MENUS =====================
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💰 فلوسي", "💵 راتب")
    kb.row("🎮 الألعاب", "📜 الأوامر")
    kb.row("🤫 همساتي", "👑 رتبتي", "ايدي")
    return kb

def games_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("كت", "حظ", "لف")
    kb.row("صراحه", "لو خيروك")
    kb.row("رجوع ⬅️")
    return kb

# ===================== HANDLERS =====================
@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user)
    bot.reply_to(message, "🤖 EVA BOT جاهز للعمل!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🎮 الألعاب")
def games(message):
    bot.reply_to(message, "🎮 قسم الألعاب", reply_markup=games_menu())

@bot.message_handler(func=lambda m: m.text == "رجوع ⬅️")
def back(message):
    bot.reply_to(message, "⬅️ القائمة الرئيسية", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "ايدي")
def id_card(message):
    u = message.from_user
    bot.reply_to(message, f"🆔 ID: {u.id}\n👤 الاسم: {u.first_name}")

# ===================== ECONOMY & GAMES =====================
@bot.message_handler(func=lambda m: m.text == "💰 فلوسي")
def money(message):
    bot.reply_to(message, f"💰 رصيدك: {get_balance(message.from_user.id)}")

@bot.message_handler(func=lambda m: m.text == "💵 راتب")
def salary(message):
    add_balance(message.from_user.id, 100)
    bot.reply_to(message, "💵 تم إضافة 100 لرصيدك")

@bot.message_handler(func=lambda m: m.text in ["حظ", "لف", "كت", "صراحه", "لو خيروك"])
def game_logic(message):
    if message.text == "حظ": bot.reply_to(message, f"🍀 نسبة حظك: {random.randint(1,100)}%")
    elif message.text == "لف": bot.reply_to(message, random.choice(["ربحت 🎉", "خسرت 💔", "جائزة 👑"]))
    elif message.text == "كت": bot.reply_to(message, random.choice(["سؤال 1", "سؤال 2"]))
    elif message.text == "صراحه": bot.reply_to(message, random.choice(["سؤال صراحة 1", "سؤال صراحة 2"]))
    elif message.text == "لو خيروك": bot.reply_to(message, random.choice(["خيار 1", "خيار 2"]))

# ===================== WHISPERS =====================
@bot.message_handler(func=lambda m: m.text and m.text.startswith("همسه"))
def whisper(message):
    try:
        parts = message.text.split("|")
        msg = parts[2]
        receiver = message.reply_to_message.from_user.id if message.reply_to_message else None
        if not receiver:
            cursor.execute("SELECT user_id FROM users WHERE username=?", (parts[1].replace("@", "").strip(),))
            receiver = cursor.fetchone()[0]
        cursor.execute("INSERT INTO whispers (sender, receiver, chat_id, msg) VALUES (?,?,?,?)", (message.from_user.id, receiver, message.chat.id, msg))
        conn.commit()
        bot.reply_to(message, "🤫 تم إرسال الهمسة")
    except Exception:
        bot.reply_to(message, "طريقة الهمسة: همسه | @user | الرسالة")

# ===================== AUTO REPLY =====================
@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def auto_reply(message):
    if message.text.startswith("اضف رد"):
        if message.from_user.id != MAIN_ID: return
        try:
            parts = message.text.split("|")
            cursor.execute("INSERT INTO replies (word, reply, image) VALUES (?,?,?)", (parts[1].strip(), parts[2].strip(), parts[3].strip() if len(parts)>3 else None))
            conn.commit()
            bot.reply_to(message, "✅ تمت الإضافة")
        except Exception:
            bot.reply_to(message, "خطأ في الصيغة")
        return

    cursor.execute("SELECT reply, image FROM replies WHERE word=?", (message.text,))
    row = cursor.fetchone()
    if row:
        reply, image = row
        if image: bot.send_photo(message.chat.id, image, caption=reply)
        else: bot.reply_to(message, reply)

# ===================== CALLBACKS: الأوامر والألعاب (Inline)
@bot.message_handler(func=lambda m: m.text == "الأوامر")
def send_main_menu(message):
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
    markup.add(types.InlineKeyboardButton("🔥 متجر روز الرقمي", url="https://t.me/your_store"))
    markup.add(types.InlineKeyboardButton("القفل والفتح", callback_data="lock_unlock_menu"))
    markup.add(types.InlineKeyboardButton("التفعيل والتعطيل", callback_data="enable_disable_menu"))
    markup.add(types.InlineKeyboardButton("رجوع ⬅️", callback_data="back_main"))
    bot.reply_to(message, "📜 أهلاً بك عزيزي في قائمة الاوامر:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "الالعاب")
def send_games_menu(message):
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
    markup.add(types.InlineKeyboardButton("رجوع ⬅️", callback_data="back_games"))
    bot.reply_to(message, "🎮 اختر لعبة للبدء:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_buttons(call):
    if not call.message or not call.message.chat or call.message.chat.type not in ("group", "supergroup"):
        try:
            bot.answer_callback_query(call.id, "❌ هذه الأوامر متاحة في المجموعات فقط.")
        except Exception:
            pass
        return

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
            markup.add(types.InlineKeyboardButton("🔥 متجر روز الرقمي", url="https://t.me/your_store"))
            markup.add(types.InlineKeyboardButton("القفل والفتح", callback_data="lock_unlock_menu"))
            markup.add(types.InlineKeyboardButton("التفعيل والتعطيل", callback_data="enable_disable_menu"))
            markup.add(types.InlineKeyboardButton("رجوع ⬅️", callback_data="back_main"))
            bot.answer_callback_query(call.id)
            bot.edit_message_text("📜 أهلاً بك عزيزي في قائمة الاوامر:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة back_main: {e}")
        return

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

    if call.data.startswith("game_"):
        try:
            uid = call.from_user.id
            # تأكد من وجود المستخدم في القاعدة
            cursor.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?,?,?)", (uid, call.from_user.username, call.from_user.first_name))
            conn.commit()

            if call.data in ("game_nawadi", "game_luck"):
                bot.edit_message_text(f"🍀 حظك اليوم: {random.randint(1,100)}%", call.message.chat.id, call.message.message_id)

            elif call.data in ("game_ghzah", "game_spin"):
                bot.edit_message_text(f"🎲 النتيجة: {random.choice(['ربحت 🎉','خسرت 💔','جائزة 👑'])}", call.message.chat.id, call.message.message_id)

            elif call.data == "game_bank":
                balance = get_balance(uid)
                if balance <= 0:
                    stake = 10
                else:
                    stake = min(max(10, balance // 10), 200)

                win = random.choice([True, False, False])
                if win:
                    gain = random.randint(stake, stake * 3)
                    add_balance(uid, gain)
                    new_bal = get_balance(uid)
                    bot.edit_message_text(f"🏦 فزت في البنك بـ {gain} 💰\nرصيدك الآن: {new_bal}", call.message.chat.id, call.message.message_id)
                else:
                    loss = stake
                    add_balance(uid, -loss)
                    new_bal = get_balance(uid)
                    bot.edit_message_text(f"🏦 خسرت في البنك {loss} 💔\nرصيدك الآن: {new_bal}", call.message.chat.id, call.message.message_id)

            elif call.data == "game_online":
                bot.edit_message_text("🔗 العاب اونلاين: افتح الرابط للعب.", call.message.chat.id, call.message.message_id)
        except Exception as e:
            logger.error(f"❌ خطأ في منطق الألعاب: {e}")
        return

    if call.data == "admin_cmds":
        text = """
• قائمة الاوامر الادمنية :

⌔ رفع ادمن
⌔ تنزيل ادمن
⌔ رفع مدير
⌔ تنزيل مدير
⌔ حظر
⌔ الغاء الحظر
The message was truncated due to length limits in tool output. Please let me know if you want me to continue.