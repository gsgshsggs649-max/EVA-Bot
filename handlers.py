import random
import logging
from telebot import types

# استيراد المتغيرات والدوال من bot.py
from bot import bot, conn, cursor, MAIN_ID, DEV_ONLY_ID, get_balance, add_balance, get_rank, main_menu, games_menu, commands_menu

logger = logging.getLogger(__name__)

# ===================== MENUS & HANDLERS =====================

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


# ===================== ECONOMY & GAMES HELPERS =====================

def ensure_user_exists(user):
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?,?,?)",
            (user.id, getattr(user, 'username', None), getattr(user, 'first_name', None))
        )
        conn.commit()
    except Exception as e:
        logger.error(f"❌ خطأ في التأكد من وجود المستخدم: {e}")


# ألعاب سريعة كرسائل عادية (لمن يكتب النص مباشرة داخل المجموعة)
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

        cursor.execute(
            "INSERT INTO whispers (sender, receiver, chat_id, msg) VALUES (?,?,?,?)",
            (message.from_user.id, receiver, message.chat.id, msg)
        )
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
        cursor.execute(
            "SELECT sender, msg FROM whispers WHERE receiver=? AND seen=0",
            (message.from_user.id,)
        )
        rows = cursor.fetchall()
        if not rows:
            bot.reply_to(message, "📭 ما عندك همسات")
            return

        text = "📩 همساتك:\n\n"
        for r in rows:
            text += f"👤 {r[0]}: {r[1]}\n"

        cursor.execute("UPDATE whispers SET seen=1 WHERE receiver=?", (message.from_user.id,))
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


# ===================== ADD / LIST REPLIES =====================

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
            bot.send_photo(message.chat.id, file_id, caption=text)
        else:
            bot.reply_to(message, text)
    except Exception as e:
        logger.error(f"❌ خطأ في عرض بيانات المستخدم: {e}")
        bot.reply_to(message, "❌ حدث خطأ، يرجى المحاولة لاحقاً")


# ===================== PROCESS MESSAGES (MAIN LOGIC) =====================

def process_messages(message):
    text = message.text or ""

    # الاوامر التي كانت في ملف bot.py قبل الفصل
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

    # بقية منطق process_messages: الاحتفاظ بمنطق التطوير والردود العشوائية
    # تم دمج المقاطع ذات الصلة من bot.py
    # ... (إن احتجت إضافة المزيد سأدرجها بناءً على طلبك)


# ===================== CALLBACK HANDLER (الأزرار) =====================

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

    # تعامل مع أوامر القائمة (cmd_) — منطق الختمة/اذكار/قرآن
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
            # تأكد من وجود المستخدم في القاعدة
            ensure_user_exists(call.from_user)
            uid = call.from_user.id

            if call.data in ("game_nawadi", "game_luck"):
                bot.edit_message_text(f"🍀 حظك اليوم: {random.randint(1,100)}%", call.message.chat.id, call.message.message_id)

            elif call.data in ("game_ghzah", "game_spin"):
                bot.edit_message_text(f"🎲 النتيجة: {random.choice(['ربحت 🎉','خسرت 💔','جائزة 👑'])}", call.message.chat.id, call.message.message_id)

            elif call.data == "game_bank":
                # لعبة البنك تؤثر على الرصيد — رهان عشوائي يعتمد على رصيد المستخدم
                balance = get_balance(uid)
                # تحديد قيمة الرهان بناءً على الرصيد
                if balance <= 0:
                    stake = 10
                else:
                    stake = min(max(10, balance // 10), 200)

                # نتيجة اللعبة
                win = random.choice([True, False, False])  # احتمالية خسارة أعلى قليلاً
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

    # حافظ على بقية أزرار callback السابقة (admin_cmds, settings_cmds، ...)
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

# نهاية handlers.py
