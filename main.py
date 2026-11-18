# main.py - DEMO BOT + SQLite Database
# আসল পাসওয়ার্ড / কুকিজ / 2FA নেওয়া হয় না, সব ডেমো ডাটা

import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
MAIN_ADMIN_ID = 123456789  # আপনার Telegram ID বসান
DB_FILE = "bot.db"

logging.basicConfig(level=logging.INFO)

# ===== DATABASE =====
def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)")
    c.execute("CREATE TABLE IF NOT EXISTS withdraws (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, status TEXT DEFAULT 'pending')")
    c.execute("CREATE TABLE IF NOT EXISTS tasks_demo (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, task_name TEXT, price TEXT, demo_field1 TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (MAIN_ADMIN_ID,))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance_off', '0')")
    conn.commit()
    conn.close()

def get_user(uid):
    conn = db(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    r = c.fetchone(); conn.close()
    return r

def ensure_user(uid, name):
    conn = db(); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, name, balance) VALUES (?,?,0)", (uid, name))
    c.execute("UPDATE users SET name=? WHERE user_id=?", (name, uid))
    conn.commit(); conn.close()

def is_admin(uid):
    conn = db(); c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE user_id=?", (uid,))
    r = c.fetchone(); conn.close()
    return r is not None

def is_maintenance_off():
    conn = db(); c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='maintenance_off'")
    r = c.fetchone(); conn.close()
    return r and r["value"] == "1"

def set_maintenance(off: bool):
    conn = db(); c = conn.cursor()
    c.execute("UPDATE settings SET value=? WHERE key='maintenance_off'", ("1" if off else "0",))
    conn.commit(); conn.close()

# ===== KEYBOARDS =====
def main_menu_kb(uid):
    kb = [
        [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
        [InlineKeyboardButton("📋 Task (Demo)", callback_data="user_tasks")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
    ]
    if is_admin(uid):
        kb.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(kb)

def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 User Management", callback_data="adm_users")],
        [InlineKeyboardButton("💸 Withdraw Management", callback_data="adm_withdraw")],
        [InlineKeyboardButton("📋 Task Management", callback_data="adm_tasks")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast")],
        [InlineKeyboardButton("🔐 Access Control", callback_data="adm_access")],
        [InlineKeyboardButton("🛠 Maintenance Mode", callback_data="adm_maint")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ])

def back_kb(cb):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=cb)]])

async def send_to_all(context, text):
    conn = db(); c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    ids = [r["user_id"] for r in c.fetchall()]
    conn.close()
    s = 0; f = 0
    for uid in ids:
        try:
            await context.bot.send_message(uid, text); s += 1
        except: f += 1
    return s, f

user_state = {}
temp_data = {}

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ensure_user(uid, update.effective_user.first_name or "User")
    if is_maintenance_off() and not is_admin(uid):
        await update.message.reply_text("বট এখন সাময়িক সময়ের জন্য বন্ধ রাখা হয়েছে")
        return
    u = get_user(uid)
    await update.message.reply_text(
        f"👋 স্বাগতম {update.effective_user.first_name}!\n💰 ব্যালেন্স: {u['balance']} টাকা",
        reply_markup=main_menu_kb(uid)
    )

# ===== CALLBACKS =====
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data
    ensure_user(uid, q.from_user.first_name or "User")

    if is_maintenance_off() and not is_admin(uid) and data != "main_menu":
        await q.edit_message_text("বট এখন সাময়িক সময়ের জন্য বন্ধ রাখা হয়েছে")
        return

    if data == "main_menu":
        user_state.pop(uid, None)
        u = get_user(uid)
        await q.edit_message_text(f"🏠 Main Menu\n💰 ব্যালেন্স: {u['balance']} টাকা", reply_markup=main_menu_kb(uid))
        return

    if data == "profile":
        u = get_user(uid)
        await q.edit_message_text(f"👤 Profile\nID: {uid}\nনাম: {q.from_user.first_name}\n💰 ব্যালেন্স: {u['balance']} টাকা", reply_markup=back_kb("main_menu"))
        return

    if data == "balance":
        u = get_user(uid)
        await q.edit_message_text(f"💰 আপনার ব্যালেন্স: {u['balance']} টাকা", reply_markup=back_kb("main_menu"))
        return

    # --- USER TASKS DEMO ---
    if data == "user_tasks":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📸 Instagram (Demo)", callback_data="ut_instagram")],
            [InlineKeyboardButton("📧 Gmail (Demo)", callback_data="ut_gmail")],
            [InlineKeyboardButton("📘 Facebook (Demo)", callback_data="ut_facebook")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ])
        await q.edit_message_text("📋 Task Management (সব ডেমো)\nএকটা বেছে নিন:", reply_markup=kb)
        return

    if data in ["ut_instagram", "ut_gmail", "ut_facebook"]:
        key = data.replace("ut_", "")
        conn = db(); c = conn.cursor()
        c.execute("SELECT * FROM tasks_demo WHERE category=?", (key,))
        rows = c.fetchall(); conn.close()
        if not rows:
            txt = "এখনো কোনো ডেমো কাজ নেই।"
        else:
            txt = "📋 ডেমো কাজের লিস্ট:\n\n"
            for i, t in enumerate(rows, 1):
                txt += f"{i}. {t['task_name']} - {t['price']} টাকা\n"
        await q.edit_message_text(txt, reply_markup=back_kb("main_menu"))
        return

    if data == "withdraw":
        user_state[uid] = "await_withdraw_amount"
        await q.edit_message_text("💸 কত টাকা Withdraw করতে চান? টাকার পরিমাণ লিখুন:")
        return

    # --- ADMIN ---
    if data == "admin_panel":
        if not is_admin(uid):
            await q.edit_message_text("আপনি অ্যাডমিন না।"); return
        await q.edit_message_text("🛠 Admin Panel", reply_markup=admin_kb())
        return

    # USER MANAGEMENT
    if data == "adm_users":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Total User", callback_data="adm_total")],
            [InlineKeyboardButton("Search User", callback_data="adm_search")],
            [InlineKeyboardButton("Add Balance", callback_data="adm_addbal")],
            [InlineKeyboardButton("Remove Balance", callback_data="adm_rembal")],
            [InlineKeyboardButton("Delete User Database History", callback_data="adm_del_hist")],
            [InlineKeyboardButton("Back", callback_data="admin_panel")],
        ])
        await q.edit_message_text("👥 User Management", reply_markup=kb); return

    if data == "adm_total":
        conn = db(); c = conn.cursor()
        c.execute("SELECT * FROM users")
        rows = c.fetchall(); conn.close()
        txt = f"👥 Total User: {len(rows)}\n\n"
        for u in rows:
            txt += f"ID: {u['user_id']} | {u['name']} | {u['balance']} টাকা\n"
        await q.edit_message_text(txt[:4000] or "কেউ নেই", reply_markup=back_kb("adm_users")); return

    if data == "adm_search":
        user_state[uid] = "adm_search"
        await q.edit_message_text("যে ইউজারকে খুঁজতে চান তার ইউজার আইডি দিন:"); return
    if data == "adm_addbal":
        user_state[uid] = "adm_addbal_id"
        await q.edit_message_text("যে ইউজারের ব্যালেন্স বাড়াতে চান তার ইউজার আইডি দিন:"); return
    if data == "adm_rembal":
        user_state[uid] = "adm_rembal_id"
        await q.edit_message_text("যে ইউজারের ব্যালেন্স কমাতে চান তার ইউজার আইডি দিন:"); return
    if data == "adm_del_hist":
        conn = db(); c = conn.cursor()
        c.execute("DELETE FROM users WHERE user_id != ?", (uid,))
        c.execute("DELETE FROM withdraws")
        c.execute("DELETE FROM tasks_demo")
        conn.commit(); conn.close()
        await q.edit_message_text("✅ User Database History ডিলিট করা হয়েছে", reply_markup=back_kb("adm_users")); return

    # WITHDRAW MANAGEMENT
    if data == "adm_withdraw":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏳ Pending", callback_data="wd_pending")],
            [InlineKeyboardButton("✅ Approve", callback_data="wd_approved")],
            [InlineKeyboardButton("❌ Reject", callback_data="wd_rejected")],
            [InlineKeyboardButton("Back", callback_data="admin_panel")],
        ])
        await q.edit_message_text("💸 Withdraw Management", reply_markup=kb); return

    if data in ["wd_pending", "wd_approved", "wd_rejected"]:
        status = {"wd_pending": "pending", "wd_approved": "approved", "wd_rejected": "rejected"}[data]
        conn = db(); c = conn.cursor()
        c.execute("SELECT * FROM withdraws WHERE status=?", (status,))
        rows = c.fetchall(); conn.close()
        if not rows:
            await q.edit_message_text(f"কোনো {status} Withdraw নেই", reply_markup=back_kb("adm_withdraw")); return
        kb = []; txt = f"💸 {status.upper()} List:\n\n"
        for w in rows:
            txt += f"ID: {w['id']} | User: {w['user_id']} | {w['amount']} টাকা\n"
            if status == "pending":
                kb.append([InlineKeyboardButton(f"✅ Approve #{w['id']}", callback_data=f"wd_appr_{w['id']}"), InlineKeyboardButton(f"❌ Reject #{w['id']}", callback_data=f"wd_rej_{w['id']}")])
        kb.append([InlineKeyboardButton("Back", callback_data="adm_withdraw")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb)); return

    if data.startswith("wd_appr_"):
        wid = int(data.split("_")[-1])
        conn = db(); c = conn.cursor()
        c.execute("SELECT * FROM withdraws WHERE id=?", (wid,))
        w = c.fetchone()
        if w:
            c.execute("UPDATE withdraws SET status='approved' WHERE id=?", (wid,))
            conn.commit()
            try: await context.bot.send_message(w["user_id"], f"✅ আপনার {w['amount']} টাকা Withdraw Approve হয়েছে।")
            except: pass
        conn.close()
        await q.edit_message_text("✅ Approve ঘরে চলে গেছে", reply_markup=back_kb("adm_withdraw")); return

    if data.startswith("wd_rej_"):
        wid = int(data.split("_")[-1])
        conn = db(); c = conn.cursor()
        c.execute("SELECT * FROM withdraws WHERE id=?", (wid,))
        w = c.fetchone()
        if w:
            c.execute("UPDATE withdraws SET status='rejected' WHERE id=?", (wid,))
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (w["amount"], w["user_id"]))
            conn.commit()
            try: await context.bot.send_message(w["user_id"], f"❌ আপনার {w['amount']} টাকা Withdraw Reject হয়েছে। ব্যালেন্স ফেরত দেওয়া হয়েছে।")
            except: pass
        conn.close()
        await q.edit_message_text("❌ Reject ঘরে চলে গেছে + ব্যালেন্স ফেরত দেওয়া হয়েছে", reply_markup=back_kb("adm_withdraw")); return

    # TASK MANAGEMENT ADMIN
    if data == "adm_tasks":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📸 Instagram (Demo)", callback_data="adm_t_instagram")],
            [InlineKeyboardButton("📧 Gmail (Demo)", callback_data="adm_t_gmail")],
            [InlineKeyboardButton("📘 Facebook (Demo)", callback_data="adm_t_facebook")],
            [InlineKeyboardButton("Back", callback_data="admin_panel")],
        ])
        await q.edit_message_text("📋 Task Management - ডেমো কাজ যোগ করুন", reply_markup=kb); return

    if data in ["adm_t_instagram", "adm_t_gmail", "adm_t_facebook"]:
        key = data.replace("adm_t_", "")
        temp_data[uid] = {"task_key": key}
        user_state[uid] = "adm_task_name"
        await q.edit_message_text("কাজের নাম এবং টাকা দিন।\nএই ফরম্যাটে লিখুন: নাম | টাকা\nউদাহরণ: Instagram 2FA | 4.00\n\nআপনি যখন তখন টাকা পরিবর্তন করতে পারবেন - নতুন করে আবার যোগ করলেই হবে।")
        return

    # BROADCAST
    if data == "adm_broadcast":
        user_state[uid] = "adm_broadcast"
        await q.edit_message_text("📢 সবাইকে পাঠাতে চান এমন মেসেজটি লিখুন:"); return

    # ACCESS CONTROL
    if data == "adm_access":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 অ্যাডমিন লিস্ট", callback_data="acc_list")],
            [InlineKeyboardButton("➕ অ্যাডমিন যোগ", callback_data="acc_add")],
            [InlineKeyboardButton("➖ অ্যাডমিন রিমুভ", callback_data="acc_remove")],
            [InlineKeyboardButton("Back", callback_data="admin_panel")],
        ])
        await q.edit_message_text("🔐 Access Control", reply_markup=kb); return
    if data == "acc_list":
        conn = db(); c = conn.cursor()
        c.execute("SELECT * FROM admins")
        rows = c.fetchall(); conn.close()
        txt = f"👥 মোট অ্যাডমিন: {len(rows)}\n\n"
        for a in rows: txt += f"ID: {a['user_id']}\n"
        await q.edit_message_text(txt, reply_markup=back_kb("adm_access")); return
    if data == "acc_add":
        user_state[uid] = "acc_add"
        await q.edit_message_text("যাকে অ্যাডমিন করবেন তার ইউজার আইডি দিন:"); return
    if data == "acc_remove":
        user_state[uid] = "acc_remove"
        await q.edit_message_text("যাকে অ্যাডমিন থেকে সরাবেন তার ইউজার আইডি দিন:"); return

    # MAINTENANCE
    if data == "adm_maint":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ বট চালু করুন", callback_data="maint_on")],
            [InlineKeyboardButton("⛔ বট বন্ধ করুন", callback_data="maint_off")],
            [InlineKeyboardButton("🔄 বট রিফ্রেশ করুন", callback_data="maint_refresh")],
            [InlineKeyboardButton("♻️ বট রিস্টার্ট করুন", callback_data="maint_restart")],
            [InlineKeyboardButton("Back", callback_data="admin_panel")],
        ])
        await q.edit_message_text(f"🛠 Maintenance Mode\nবর্তমান: {'বন্ধ' if is_maintenance_off() else 'চালু'}", reply_markup=kb); return
    if data == "maint_on":
        set_maintenance(False)
        s, f = await send_to_all(context, "✅ বট এখন চালু হয়েছে।")
        await q.edit_message_text(f"✅ বট চালু হয়েছে। মেসেজ পেয়েছে {s} জন, ব্যর্থ {f} জন", reply_markup=back_kb("adm_maint")); return
    if data == "maint_off":
        set_maintenance(True)
        s, f = await send_to_all(context, "⛔ বট এখন সাময়িক সময়ের জন্য বন্ধ রাখা হয়েছে।")
        await q.edit_message_text(f"⛔ বট বন্ধ হয়েছে। মেসেজ পেয়েছে {s} জন", reply_markup=back_kb("adm_maint")); return
    if data == "maint_refresh":
        await q.edit_message_text("🔄 বট রিফ্রেশ করা হয়েছে (শুরু থেকে শেষ পর্যন্ত)", reply_markup=back_kb("adm_maint")); return
    if data == "maint_restart":
        await q.edit_message_text("♻️ বট রিস্টার্ট হয়েছে। কোনো ডাটা ডিলিট হয়নি, বট এখন দ্রুত কাজ করবে।", reply_markup=back_kb("adm_maint")); return

# ===== TEXT =====
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    state = user_state.get(uid)
    ensure_user(uid, update.effective_user.first_name or "User")

    if is_maintenance_off() and not is_admin(uid):
        await update.message.reply_text("বট এখন সাময়িক সময়ের জন্য বন্ধ রাখা হয়েছে"); return

    if state == "await_withdraw_amount":
        try:
            amt = float(text)
            u = get_user(uid)
            if u["balance"] < amt:
                await update.message.reply_text("❌ ব্যালেন্স যথেষ্ট নেই।"); return
            conn = db(); c = conn.cursor()
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amt, uid))
            c.execute("INSERT INTO withdraws (user_id, amount, status) VALUES (?,?, 'pending')", (uid, amt))
            wid = c.lastrowid
            conn.commit(); conn.close()
            user_state.pop(uid, None)
            await update.message.reply_text(f"✅ Withdraw রিকোয়েস্ট পাঠানো হয়েছে। ID: {wid} | {amt} টাকা | Pending")
        except: await update.message.reply_text("সঠিক টাকার পরিমাণ লিখুন।")
        return

    if state == "adm_search":
        user_state.pop(uid, None)
        try:
            u = get_user(int(text))
            await update.message.reply_text(f"ID: {text}\nপাওয়া গেছে: {dict(u) if u else 'নেই'}")
        except: await update.message.reply_text("সঠিক আইডি দিন।")
        return

    if state == "adm_addbal_id":
        if text.isdigit():
            temp_data[uid] = {"target": int(text)}
            user_state[uid] = "adm_addbal_amt"
            await update.message.reply_text("কত টাকা বাড়াতে চান সেটা লিখুন:")
        else: await update.message.reply_text("সঠিক আইডি দিন।")
        return
    if state == "adm_addbal_amt":
        target = temp_data.get(uid, {}).get("target")
        try:
            amt = float(text)
            conn = db(); c = conn.cursor()
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amt, target))
            conn.commit(); conn.close()
            u = get_user(target)
            if u:
                try: await context.bot.send_message(target, f"✅ আপনার ব্যালেন্সে {amt} টাকা যোগ করা হয়েছে। নতুন ব্যালেন্স: {u['balance']} টাকা")
                except: pass
                await update.message.reply_text(f"✅ {target} এর ব্যালেন্স {amt} টাকা বাড়ানো হয়েছে।")
            else: await update.message.reply_text("ইউজার পাওয়া যায়নি।")
        except: await update.message.reply_text("সঠিক টাকা লিখুন।")
        user_state.pop(uid, None); return

    if state == "adm_rembal_id":
        if text.isdigit():
            temp_data[uid] = {"target": int(text)}
            user_state[uid] = "adm_rembal_amt"
            await update.message.reply_text("কত টাকা কমাতে চান সেটা লিখুন:")
        else: await update.message.reply_text("সঠিক আইডি দিন।")
        return
    if state == "adm_rembal_amt":
        target = temp_data.get(uid, {}).get("target")
        try:
            amt = float(text)
            conn = db(); c = conn.cursor()
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amt, target))
            conn.commit(); conn.close()
            u = get_user(target)
            if u:
                try: await context.bot.send_message(target, f"⚠️ আপনার ব্যালেন্স থেকে {amt} টাকা কমানো হয়েছে। নতুন ব্যালেন্স: {u['balance']} টাকা")
                except: pass
                await update.message.reply_text(f"✅ {target} এর ব্যালেন্স {amt} টাকা কমানো হয়েছে।")
            else: await update.message.reply_text("ইউজার পাওয়া যায়নি।")
        except: await update.message.reply_text("সঠিক টাকা লিখুন।")
        user_state.pop(uid, None); return

    if state == "adm_task_name":
        try:
            name, price = text.split("|")
            temp_data[uid]["task_name"] = name.strip()
            temp_data[uid]["price"] = price.strip()
            user_state[uid] = "adm_task_demo_field"
            await update.message.reply_text("এখন ডেমো ফিল্ড ১ দিন (আসল কিছু না, যেমন demo_text_1):")
        except:
            await update.message.reply_text("এইভাবে লিখুন: নাম | টাকা\nযেমন: Instagram 2FA | 4.00")
        return

    if state == "adm_task_demo_field":
        d = temp_data.get(uid, {})
        conn = db(); c = conn.cursor()
        c.execute("INSERT INTO tasks_demo (category, task_name, price, demo_field1) VALUES (?,?,?,?)", (d.get("task_key"), d.get("task_name"), d.get("price"), text))
        conn.commit(); conn.close()
        user_state.pop(uid, None)
        await update.message.reply_text("✅ কাজ সফলভাবে যুক্ত হয়েছে (Demo)", reply_markup=admin_kb())
        return

    if state == "adm_broadcast":
        user_state.pop(uid, None)
        s, f = await send_to_all(context, text)
        await update.message.reply_text(f"✅ মেসেজ সফল\nপাঠানো হয়েছে ১ টি\nমেসেজ পেয়েছে {s} জন\nমেসেজ ব্যর্থ হয়েছে {f} জন")
        return

    if state == "acc_add":
        user_state.pop(uid, None)
        try:
            t = int(text)
            ensure_user(t, "New Admin")
            conn = db(); c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (t,))
            conn.commit(); conn.close()
            try: await context.bot.send_message(t, "🎉 আপনাকে অ্যাডমিন করা হয়েছে।")
            except: pass
            await update.message.reply_text(f"✅ {t} কে অ্যাডমিন করা হয়েছে। মেসেজ চলে গেছে।")
        except: await update.message.reply_text("সঠিক আইডি দিন।")
        return

    if state == "acc_remove":
        user_state.pop(uid, None)
        try:
            t = int(text)
            if t == MAIN_ADMIN_ID:
                await update.message.reply_text("❌ মেইন অ্যাডমিনকে সরানো যাবে না।"); return
            conn = db(); c = conn.cursor()
            c.execute("DELETE FROM admins WHERE user_id=?", (t,))
            conn.commit(); conn.close()
            try: await context.bot.send_message(t, "⚠️ আপনাকে অ্যাডমিন থেকে সরিয়ে দেওয়া হয়েছে।")
            except: pass
            await update.message.reply_text(f"✅ {t} কে অ্যাডমিন থেকে সরানো হয়েছে।")
        except: await update.message.reply_text("সঠিক আইডি দিন।")
        return

    await update.message.reply_text("🏠 মেনু দেখতে /start লিখুন", reply_markup=main_menu_kb(uid))

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    print("Bot running with SQLite...")
    app.run_polling()

if __name__ == "__main__":
    main()
