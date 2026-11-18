import os, sqlite3, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUPPORT_BOT = "@Nexora_X_Support_Bot"
SUBMISSION_CHANNEL = "https://t.me/Nexora_X_Submission"

# ---------- DB ----------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 0, total_income REAL DEFAULT 0, done INTEGER DEFAULT 0, pending INTEGER DEFAULT 0, rejected INTEGER DEFAULT 0, lang TEXT DEFAULT 'bn', ref_by INTEGER DEFAULT 0, ref_earn REAL DEFAULT 0)")
cur.execute("CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, title TEXT, price REAL, data TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS withdraws (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, method TEXT, number TEXT, amount REAL, status TEXT DEFAULT 'pending')")
cur.execute("CREATE TABLE IF NOT EXISTS gift_codes (code TEXT PRIMARY KEY, amount REAL, used_by TEXT DEFAULT '')")
cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
cur.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance','off')")
conn.commit()

def get_user(uid, name=""):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    r = cur.fetchone()
    if not r:
        cur.execute("INSERT INTO users (id,name) VALUES (?,?)", (uid, name))
        conn.commit()
    return r

def is_admin(uid):
    if uid == OWNER_ID: return True
    cur.execute("SELECT * FROM admins WHERE id=?", (uid,))
    return cur.fetchone() is not None

def is_maintenance():
    cur.execute("SELECT value FROM settings WHERE key='maintenance'")
    return cur.fetchone()[0] == 'on'

def get_lang(uid):
    cur.execute("SELECT lang FROM users WHERE id=?", (uid,))
    r = cur.fetchone()
    return r[0] if r else 'bn'

# ---------- Keyboards ----------
def user_menu(uid):
    # Admin button only for admin/owner
    kb = [
        [InlineKeyboardButton("💼 কাজ", callback_data="tasks")],
        [InlineKeyboardButton("💵 ব্যালেন্স", callback_data="balance")],
        [InlineKeyboardButton("📤 টাকা উত্তোলন", callback_data="withdraw")],
        [InlineKeyboardButton("👥 মাই রেফারেল", callback_data="referral")],
        [InlineKeyboardButton("📞 সাপোর্ট", callback_data="support")],
        [InlineKeyboardButton("🎁🗄 গিফট কোড", callback_data="gift")],
        [InlineKeyboardButton("🌐 ভাষা পরিবর্তন", callback_data="lang")],
        [InlineKeyboardButton("🤝 পার্টনার বট", callback_data="partner")],
    ]
    if is_admin(uid):
        kb.append([InlineKeyboardButton("🛡 অ্যাডমিন প্যানেল", callback_data="admin")])
    return InlineKeyboardMarkup(kb)

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 User Management", callback_data="adm_users")],
        [InlineKeyboardButton("💸 Withdraw Management", callback_data="adm_withdraw")],
        [InlineKeyboardButton("📋 Task Management", callback_data="adm_tasks")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast")],
        [InlineKeyboardButton("🔐 Access Control", callback_data="adm_access")],
        [InlineKeyboardButton("🛠 Maintenance Mode", callback_data="adm_maint")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ])

# ---------- Start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    get_user(uid, name)
    # Referral
    if context.args:
        try:
            ref = int(context.args[0].replace("start_", ""))
            if ref != uid:
                cur.execute("UPDATE users SET ref_by=? WHERE id=? AND ref_by=0", (ref, uid))
                conn.commit()
        except: pass
    if is_maintenance() and not is_admin(uid):
        await update.message.reply_text("বট এখন সাময়িক সময়ের জন্য বন্ধ রাখা হয়েছে")
        return
    await update.message.reply_text(f"🥰 স্বাগতম, {name}!\n💎কাজ শুরু করতে নিচের অপশনগুলো ব্যবহার করুন 🔽", reply_markup=user_menu(uid))

# ---------- Callback ----------
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data
    get_user(uid, q.from_user.first_name)
    if is_maintenance() and not is_admin(uid) and data not in ["main_menu"]:
        await q.edit_message_text("বট এখন সাময়িক সময়ের জন্য বন্ধ রাখা হয়েছে", reply_markup=user_menu(uid))
        return

    if data == "main_menu":
        await q.edit_message_text(f"🥰 স্বাগতম, {q.from_user.first_name}!\n💎কাজ শুরু করতে নিচের অপশনগুলো ব্যবহার করুন 🔽", reply_markup=user_menu(uid))

    elif data == "balance":
        cur.execute("SELECT balance,total_income,done,pending,rejected FROM users WHERE id=?", (uid,))
        b, ti, d, p, r = cur.fetchone()
        cur.execute("SELECT COALESCE(SUM(amount),0) FROM withdraws WHERE user_id=? AND status='pending'", (uid,))
        pend = cur.fetchone()[0]
        await q.edit_message_text(f"💵 আপনার ব্যালেন্স\n━━━━━━━━━━━━━━━━━━━━━━\n💵 ব্যালেন্স: {b:.2f} BDT\n💸 পেন্ডিং (উইথড্র): {pend:.2f} BDT\n💰টোটাল ইনকাম: {ti:.2f} টাকা\n━━━━━━━━━━━━━━━━━━━━━━\n✅ সম্পন্ন কাজ: {d} টি\n⏳রিভিউতে আছে: {p} টি\n❌ রিজেক্টেড: {r} টি", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]))

    elif data == "tasks":
        cur.execute("SELECT id,type,title,price FROM tasks")
        rows = cur.fetchall()
        if not rows:
            await q.edit_message_text("এখনো কোনো কাজ নেই। পরে আবার চেষ্টা করুন।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]))
            return
        kb = [[InlineKeyboardButton(f"{t[1]} | {t[2]} - {t[3]} BDT", callback_data=f"task_{t[0]}")] for t in rows]
        kb.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await q.edit_message_text("💼 কাজগুলো নিচে দেওয়া হলো:", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("task_"):
        tid = data.split("_")[1]
        cur.execute("SELECT type,title,price,data FROM tasks WHERE id=?", (tid,))
        t = cur.fetchone()
        if not t: return
        await q.edit_message_text(f"📋 কাজ: {t[1]}\n💰 দাম: {t[2]} BDT\n\nকাজটি করতে নিচের তথ্য পাঠান।\nএডমিন রিভিউ করার পর ব্যালেন্স যোগ হবে।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 সাবমিট করেছি", callback_data=f"submit_{tid}")],[InlineKeyboardButton("🔙 Back", callback_data="tasks")]]))

    elif data == "withdraw":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("USDT (BEP-20) -> সর্বনিম্ন: 0.25(-0.05)", callback_data="wd_usdt")],
            [InlineKeyboardButton("বিকাশ -> সর্বনিম্ন: ১১০৳(-১০)", callback_data="wd_bkash")],
            [InlineKeyboardButton("নগদ", callback_data="wd_nagad")],
            [InlineKeyboardButton("রকেট", callback_data="wd_rocket")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ])
        await q.edit_message_text("📤 টাকা তোলার মাধ্যম সিলেক্ট করুন:", reply_markup=kb)

    elif data == "wd_usdt":
        await q.edit_message_text("⚠️ USDT (BEP-20) উত্তোলন বর্তমানে বন্ধ আছে।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="withdraw")]]))
    elif data in ["wd_bkash","wd_nagad","wd_rocket"]:
        method = {"wd_bkash":"বিকাশ","wd_nagad":"নগদ","wd_rocket":"রকেট"}[data]
        context.user_data["wd_method"] = method
        context.user_data["step"] = "wd_number"
        await q.edit_message_text(f"📝 আপনার {method} নাম্বার দিন:")

    elif data == "referral":
        cur.execute("SELECT COUNT(*), COALESCE(SUM(ref_earn),0) FROM users WHERE ref_by=?", (uid,))
        # ref count
        cur.execute("SELECT COUNT(*) FROM users WHERE ref_by=?", (uid,))
        cnt = cur.fetchone()[0]
        cur.execute("SELECT ref_earn FROM users WHERE id=?", (uid,))
        earn = cur.fetchone()[0]
        await q.edit_message_text(f"👤 মোট রেফার: {cnt}\n😃 মোট রেফারেল আয়: {earn:.2f} BDT\n🔗 আপনার রেফার লিংক:\nhttps://t.me/Nexora_X_Earn_Bot?start={uid}\n\nℹ️ আপনি আপনার প্রতিটি রেফারেলের সম্পূর্ণ করা কাজ থেকে আয়ের 10% কমিশন পাবেন।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]))

    elif data == "support":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("👨‍💻 অ্যাডমিন সাপোর্ট", url=f"https://t.me/{SUPPORT_BOT.replace('@','')}")],
            [InlineKeyboardButton("📋 সাবমিশন চ্যানেল", url=SUBMISSION_CHANNEL)],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ])
        await q.edit_message_text("📞 গ্রাহক সেবা কেন্দ্র\n━━━━━━━━━━━━━━━━━━━━━━\n\nসম্মানিত মেম্বার,\nআপনার যেকোনো সমস্যা বা জিজ্ঞাসার জন্য আমাদের সাপোর্ট টিমের সাথে যোগাযোগ করুন। আমরা দ্রুত সমাধানের চেষ্টা করব।\n⚠️ নোট: অযথা মেসেজ দেওয়া থেকে বিরত থাকুন।\nধন্যবাদ!", reply_markup=kb)

    elif data == "gift":
        context.user_data["step"] = "gift_code"
        await q.edit_message_text("🎁 গিফট কোড\n\nআপনার গিফট কোডের সিক্রেট কী লিখে পাঠান:")

    elif data == "lang":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ])
        await q.edit_message_text("ভাষা নির্বাচন করুন / Select Language:", reply_markup=kb)
    elif data.startswith("lang_"):
        lang = data.split("_")[1]
        cur.execute("UPDATE users SET lang=? WHERE id=?", (lang, uid))
        conn.commit()
        txt = "ভাষা বাংলা করা হয়েছে। বটের সব বাটন, কোড, কাজ সব এখন বাংলা হবে।" if lang=="bn" else "Language set to English. All buttons and tasks will now be in English."
        await q.edit_message_text(txt, reply_markup=user_menu(uid))

    elif data == "partner":
        await q.edit_message_text(f"😭 আপনার পার্টনার বট প্রোগ্রাম বর্তমানে বন্ধ আছে।\n\n✅ আপনার এক্সেস চালু করতে অ্যাডমিনের সাথে যোগাযোগ করুন⤵️\n➡️INBOX - {SUPPORT_BOT}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]))

    # ---- ADMIN ----
    elif data == "admin":
        if not is_admin(uid): return
        await q.edit_message_text("🛡 অ্যাডমিন প্যানেল", reply_markup=admin_menu())

    elif data == "adm_users":
        if not is_admin(uid): return
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Total User: {total}", callback_data="adm_users")],
            [InlineKeyboardButton("🔍 Search User", callback_data="adm_search")],
            [InlineKeyboardButton("➕ Add Balance", callback_data="adm_addbal")],
            [InlineKeyboardButton("➖ Remove Balance", callback_data="adm_removebal")],
            [InlineKeyboardButton("🗑 Delete User Database History", callback_data="adm_deluser")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin")],
        ])
        await q.edit_message_text("👥 User Management", reply_markup=kb)

    elif data in ["adm_search","adm_addbal","adm_removebal","adm_deluser"]:
        context.user_data["step"] = data
        prompts = {"adm_search":"Search করতে User ID পাঠান:", "adm_addbal":"Add Balance: User ID পাঠান:", "adm_removebal":"Remove Balance: User ID পাঠান:", "adm_deluser":"Delete করতে User ID পাঠান:"}
        await q.edit_message_text(prompts[data])

    elif data == "adm_withdraw":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏳ Pending", callback_data="wd_list_pending")],
            [InlineKeyboardButton("✅ Approve", callback_data="wd_list_approve")],
            [InlineKeyboardButton("❌ Reject", callback_data="wd_list_reject")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin")],
        ])
        await q.edit_message_text("💸 Withdraw Management", reply_markup=kb)

    elif data.startswith("wd_list_"):
        status = data.replace("wd_list_","")
        if status=="approve": status="approved"
        if status=="reject": status="rejected"
        cur.execute("SELECT id,user_id,method,amount FROM withdraws WHERE status=?", (status,))
        rows = cur.fetchall()
        if not rows:
            await q.edit_message_text(f"{status} এ কোনো উইথড্র নেই।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_withdraw")]]))
            return
        kb=[]
        for r in rows:
            kb.append([InlineKeyboardButton(f"#{r[0]} | {r[1]} | {r[2]} | {r[3]}", callback_data=f"wd_view_{r[0]}")])
        kb.append([InlineKeyboardButton("🔙 Back", callback_data="adm_withdraw")])
        await q.edit_message_text(f"💸 {status} লিস্ট:", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("wd_view_"):
        wid = data.split("_")[2]
        cur.execute("SELECT user_id,method,number,amount,status FROM withdraws WHERE id=?", (wid,))
        r = cur.fetchone()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"wd_approve_{wid}")],
            [InlineKeyboardButton("❌ Reject", callback_data=f"wd_reject_{wid}")],
            [InlineKeyboardButton("🔙 Back", callback_data="adm_withdraw")],
        ])
        await q.edit_message_text(f"ID: #{wid}\nUser: {r[0]}\nMethod: {r[1]}\nNumber: {r[2]}\nAmount: {r[3]}\nStatus: {r[4]}", reply_markup=kb)

    elif data.startswith("wd_approve_"):
        wid = data.split("_")[2]
        cur.execute("UPDATE withdraws SET status='approved' WHERE id=?", (wid,))
        conn.commit()
        await q.edit_message_text(f"✅ #{wid} Approved হয়েছে।", reply_markup=admin_menu())
        # notify user
        cur.execute("SELECT user_id,amount,method FROM withdraws WHERE id=?", (wid,))
        u, amt, meth = cur.fetchone()
        try: await context.bot.send_message(u, f"✅ আপনার উইথড্র Approve হয়েছে।\n💰 Amount: {amt}\nMethod: {meth}")
        except: pass

    elif data.startswith("wd_reject_"):
        wid = data.split("_")[2]
        cur.execute("SELECT user_id,amount FROM withdraws WHERE id=?", (wid,))
        u, amt = cur.fetchone()
        cur.execute("UPDATE withdraws SET status='rejected' WHERE id=?", (wid,))
        cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (amt, u))
        conn.commit()
        await q.edit_message_text(f"❌ #{wid} Rejected, ব্যালেন্স ফিরিয়ে দেওয়া হয়েছে।", reply_markup=admin_menu())
        try: await context.bot.send_message(u, f"❌ আপনার উইথড্র Reject হয়েছে। ব্যালেন্স ফিরিয়ে দেওয়া হয়েছে: {amt} BDT")
        except: pass

    elif data == "adm_tasks":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📸 Instagram Task যোগ করুন", callback_data="task_add_ig")],
            [InlineKeyboardButton("📧 Gmail Task যোগ করুন", callback_data="task_add_gmail")],
            [InlineKeyboardButton("📘 Facebook Task যোগ করুন", callback_data="task_add_fb")],
            [InlineKeyboardButton("📋 সব Task দেখুন", callback_data="task_list")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin")],
        ])
        await q.edit_message_text("📋 Task Management - Instagram / Gmail / Facebook", reply_markup=kb)

    elif data in ["task_add_ig","task_add_gmail","task_add_fb"]:
        context.user_data["step"] = data
        context.user_data["task_tmp"] = {}
        prompts = {"task_add_ig":"Instagram: কাজের নাম + টাকা দিন (যেমন: Follow | 10)", "task_add_gmail":"Gmail: কাজের নাম + টাকা দিন (যেমন: Gmail Create | 15)", "task_add_fb":"Facebook: কাজের নাম + টাকা দিন (যেমন: FB Create | 20)"}
        await q.edit_message_text(prompts[data])
    elif data == "task_list":
        cur.execute("SELECT id,type,title,price FROM tasks")
        rows = cur.fetchall()
        txt = "\n".join([f"{r[0]}. {r[1]} - {r[2]} - {r[3]} BDT" for r in rows]) or "কোনো Task নেই"
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="adm_tasks")]]))

    elif data == "adm_broadcast":
        context.user_data["step"] = "broadcast"
        await q.edit_message_text("📢 Broadcast Message পাঠান (সব ইউজারদের কাছে যাবে):")

    elif data == "adm_access":
        if uid != OWNER_ID:
            await q.edit_message_text("⚠️ শুধু Owner এই অপশন ব্যবহার করতে পারবে।", reply_markup=admin_menu())
            return
        cur.execute("SELECT id FROM admins")
        lst = ", ".join([str(r[0]) for r in cur.fetchall()]) or "কেউ নেই"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 অ্যাডমিন লিস্ট", callback_data="adm_access")],
            [InlineKeyboardButton("➕ অ্যাডমিন যোগ", callback_data="adm_addadmin")],
            [InlineKeyboardButton("➖ অ্যাডমিন রিমুভ", callback_data="adm_remadmin")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin")],
        ])
        await q.edit_message_text(f"🔐 Access Control\nঅ্যাডমিন লিস্ট: {lst}\n\nআপনি কাকে অ্যাডমিন করবেন সব আপনি করবেন। অন্য কেউ আপনাকে না বলে আপনাকে অ্যাডমিন থেকে সরাতে পারবে না।", reply_markup=kb)
    elif data in ["adm_addadmin","adm_remadmin"]:
        context.user_data["step"] = data
        await q.edit_message_text("অ্যাডমিনের User ID পাঠান:")

    elif data == "adm_maint":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ বট চালু করুন", callback_data="maint_on")],
            [InlineKeyboardButton("⛔ বট বন্ধ করুন", callback_data="maint_off")],
            [InlineKeyboardButton("🔄 বট রিফ্রেশ করুন", callback_data="maint_refresh")],
            [InlineKeyboardButton("♻️ বট রিস্টার্ট করুন", callback_data="maint_restart")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin")],
        ])
        await q.edit_message_text("🛠 Maintenance Mode", reply_markup=kb)
    elif data in ["maint_on","maint_off","maint_refresh","maint_restart"]:
        if data == "maint_on":
            cur.execute("UPDATE settings SET value='off' WHERE key='maintenance'"); conn.commit()
            msg = "✅ বট চালু করা হয়েছে"
        elif data == "maint_off":
            cur.execute("UPDATE settings SET value='on' WHERE key='maintenance'"); conn.commit()
            msg = "⛔ বট বন্ধ করা হয়েছে"
        elif data == "maint_refresh":
            msg = "🔄 বট রিফ্রেশ করা হয়েছে - শুরু থেকে শেষ পর্যন্ত"
        else:
            msg = "♻️ বট রিস্টার্ট হয়েছে। কোনো ডাটাবেজ / টাকা / কোড ডিলিট হয়নি, শুধু আপডেট হয়েছে। বট আরো দ্রুত কাজ করবে।"
        await q.edit_message_text(msg, reply_markup=admin_menu())
        # broadcast to all users
        if data in ["maint_on","maint_off"]:
            cur.execute("SELECT id FROM users")
            for (u,) in cur.fetchall():
                try: await context.bot.send_message(u, msg)
                except: pass

# ---------- Text Handler ----------
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    txt = update.message.text.strip()
    step = context.user_data.get("step","")
    get_user(uid, update.effective_user.first_name)

    # Withdraw number
    if step == "wd_number":
        context.user_data["wd_number"] = txt
        context.user_data["step"] = "wd_amount"
        await update.message.reply_text("💰 টাকার পরিমাণ লিখুন:")
        return
    if step == "wd_amount":
        try: amt = float(txt)
        except:
            await update.message.reply_text("সঠিক পরিমাণ লিখুন")
            return
        method = context.user_data.get("wd_method","বিকাশ")
        number = context.user_data.get("wd_number","")
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cur.fetchone()[0]
        if amt < 110 and method in ["বিকাশ","নগদ","রকেট"]:
            await update.message.reply_text("সর্বনিম্ন ১১০৳ লাগবে")
            return
        if amt > bal:
            await update.message.reply_text("ব্যালেন্স যথেষ্ট নেই")
            return
        cur.execute("UPDATE users SET balance=balance-? WHERE id=?", (amt, uid))
        cur.execute("INSERT INTO withdraws (user_id,method,number,amount) VALUES (?,?,?,?)", (uid, method, number, amt))
        wid = cur.lastrowid
        conn.commit()
        context.user_data["step"] = ""
        await update.message.reply_text(f"✅ #{10800+wid} Payment Completed\n🗣 User Name: {update.effective_user.first_name}\n💰 Amount: ${amt*0.009:.4f} USDT\n✅ আপনার উইথড্র রিকোয়েস্ট সফলভাবে গ্রহণ করা হয়েছে : 🔷 {method}\n🕐 নাম্বার: {number}\n🔗 পরিমাণ: {amt} টাকা")
        # notify admins
        cur.execute("SELECT id FROM admins")
        for (a,) in cur.fetchall():
            try: await context.bot.send_message(a, f"🆕 নতুন উইথড্র #{wid}\nUser: {uid}\nMethod: {method}\nAmount: {amt}\nNumber: {number}")
            except: pass
        if OWNER_ID:
            try: await context.bot.send_message(OWNER_ID, f"🆕 নতুন উইথড্র #{wid}\nUser: {uid}\nMethod: {method}\nAmount: {amt}\nNumber: {number}")
            except: pass
        return

    # Gift code
    if step == "gift_code":
        cur.execute("SELECT amount,used_by FROM gift_codes WHERE code=?", (txt,))
        r = cur.fetchone()
        if not r:
            await update.message.reply_text("❌ ভুল গিফট কোড")
            return
        if str(uid) in r[1].split(","):
            await update.message.reply_text("এই কোড আগেই ব্যবহার করেছেন")
            return
        amt = r[0]
        cur.execute("UPDATE users SET balance=balance+?, total_income=total_income+? WHERE id=?", (amt, amt, uid))
        cur.execute("UPDATE gift_codes SET used_by=? WHERE code=?", (r[1]+f",{uid}", txt))
        conn.commit()
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cur.fetchone()[0]
        context.user_data["step"] = ""
        await update.message.reply_text(f"🎉 অভিনন্দন!\n\n✨ গিফট কোড সফলভাবে ক্লেইম হয়েছে।\n\n💸 আপনি পেয়েছেন: {amt} টাকা\n💸 বর্তমান ব্যালেন্স: {bal:.2f} BDT")
        return

    # Broadcast
    if step == "broadcast":
        cur.execute("SELECT id FROM users")
        users = cur.fetchall()
        ok = fail = 0
        for (u,) in users:
            try:
                await context.bot.send_message(u, txt); ok+=1
            except: fail+=1
        context.user_data["step"] = ""
        await update.message.reply_text(f"মেসেজ সফল\nপাঠানো হয়েছে ১ টি\nমেসেজ পেয়েছে {ok} জন\nমেসেজ ব্যর্থ হয়েছে {fail} জন")
        return

    # Admin add/remove balance
    if step in ["adm_addbal","adm_removebal"]:
        if "target_id" not in context.user_data:
            try: context.user_data["target_id"] = int(txt)
            except: await update.message.reply_text("সঠিক ID দিন"); return
            await update.message.reply_text("টাকার পরিমাণ লিখুন:")
            return
        else:
            try: amt = float(txt)
            except: await update.message.reply_text("সঠিক টাকা দিন"); return
            tid = context.user_data.pop("target_id")
            if step == "adm_addbal":
                cur.execute("UPDATE users SET balance=balance+?, total_income=total_income+? WHERE id=?", (amt, amt, tid))
                msg = f"✅ আপনার ব্যালেন্সে {amt} BDT যোগ করা হয়েছে"
            else:
                cur.execute("UPDATE users SET balance=balance-? WHERE id=?", (amt, tid))
                msg = f"➖ আপনার ব্যালেন্স থেকে {amt} BDT কাটা হয়েছে"
            conn.commit()
            context.user_data["step"] = ""
            await update.message.reply_text("✅ হয়ে গেছে")
            try: await context.bot.send_message(tid, msg)
            except: pass
            return

    if step == "adm_search":
        try: tid = int(txt)
        except: await update.message.reply_text("সঠিক ID"); return
        cur.execute("SELECT name,balance,total_income,done FROM users WHERE id=?", (tid,))
        r = cur.fetchone()
        context.user_data["step"] = ""
        await update.message.reply_text(f"User: {r}" if r else "User পাওয়া যায়নি")
        return

    if step == "adm_deluser":
        try: tid = int(txt)
        except: return
        cur.execute("DELETE FROM users WHERE id=?", (tid,))
        cur.execute("DELETE FROM withdraws WHERE user_id=?", (tid,))
        conn.commit()
        context.user_data["step"] = ""
        await update.message.reply_text("✅ User Database History Delete হয়েছে")
        return

    if step in ["adm_addadmin","adm_remadmin"]:
        try: tid = int(txt)
        except: return
        if step == "adm_addadmin":
            cur.execute("INSERT OR IGNORE INTO admins VALUES (?)", (tid,)); conn.commit()
            try: await context.bot.send_message(tid, "🎉 আপনাকে অ্যাডমিন করা হয়েছে!")
            except: pass
            await update.message.reply_text("✅ অ্যাডমিন যোগ করা হয়েছে")
        else:
            if tid == OWNER_ID:
                await update.message.reply_text("⚠️ Owner কে রিমুভ করা যাবে না")
                return
            cur.execute("DELETE FROM admins WHERE id=?", (tid,)); conn.commit()
            await update.message.reply_text("✅ অ্যাডমিন রিমুভ করা হয়েছে")
        context.user_data["step"] = ""
        return

    # Task Add - simple flow: Title | Price -> then second step asks for fields
    if step in ["task_add_ig","task_add_gmail","task_add_fb"]:
        # Expected: Title | Price
        try:
            title, price = txt.split("|")
            price = float(price.strip())
        except:
            await update.message.reply_text("এইভাবে লিখুন: কাজের নাম | টাকা\nযেমন: Follow | 10")
            return
        typ = {"task_add_ig":"Instagram","task_add_gmail":"Gmail","task_add_fb":"Facebook"}[step]
        cur.execute("INSERT INTO tasks (type,title,price,data) VALUES (?,?,?,?)", (typ, title.strip(), price, ""))
        conn.commit()
        context.user_data["step"] = f"task_fields_{cur.lastrowid}"
        if typ=="Instagram":
            await update.message.reply_text("এখন ইউজারনেম + পাসওয়ার্ড দিন (যেমন: user123 | pass123)\nঘর ৩টা: ইউজারনেম, পাসওয়ার্ড, 2FA Key")
        elif typ=="Gmail":
            await update.message.reply_text("এখন প্রথম নাম -> শেষ নাম -> ইমেইল -> পাসওয়ার্ড দিন")
        else:
            await update.message.reply_text("এখন প্রথম নাম -> শেষ নাম -> পাসওয়ার্ড দিন\nঘর ৪টা: প্রথম নাম, শেষ নাম, UID, কুকিজ")
        return

    if step and step.startswith("task_fields_"):
        tid = step.split("_")[2]
        cur.execute("UPDATE tasks SET data=? WHERE id=?", (txt, tid))
        conn.commit()
        context.user_data["step"] = ""
        await update.message.reply_text("✅ কাজ সফলভাবে যুক্ত হয়েছে।")
        return

    # Default - if user sends gift code directly without button, ignore
    await update.message.reply_text("মেনু থেকে অপশন বেছে নিন 👇", reply_markup=user_menu(uid))

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
