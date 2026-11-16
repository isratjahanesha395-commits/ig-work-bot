import os, sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [9292138695]
DB = "bot.db"

def db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, total_income REAL DEFAULT 0, pending REAL DEFAULT 0, done INTEGER DEFAULT 0, review INTEGER DEFAULT 0, rejected INTEGER DEFAULT 0, refer_by INTEGER, lang TEXT DEFAULT 'bn', refer_income REAL DEFAULT 0)")
    con.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, desc TEXT, reward REAL, link TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS giftcodes (code TEXT PRIMARY KEY, amount REAL, used_by TEXT DEFAULT '')")
    con.execute("CREATE TABLE IF NOT EXISTS withdraws (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, method TEXT, number TEXT, amount REAL, status TEXT DEFAULT 'pending')")
    con.execute("CREATE TABLE IF NOT EXISTS submissions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, task_id INTEGER, proof TEXT, status TEXT DEFAULT 'pending')")
    con.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    con.commit(); return con

def get_user(uid, refer_by=None):
    con=db(); cur=con.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (id, refer_by) VALUES (?,?)", (uid, refer_by)); con.commit()
    con.close()
def get_lang(uid):
    con=db(); cur=con.cursor(); cur.execute("SELECT lang FROM users WHERE id=?", (uid,)); r=cur.fetchone(); con.close(); return r[0] if r else 'bn'

T = {
 'bn': {
  'welcome': "👋 আসসালামু আলাইকুম!\n\n🌟 Nexora X Earn এ স্বাগতম!\n\nনিচে থেকে যেকোনো কাজ করে টাকা ইনকাম করতে পারবেন।\n\n👇 নিচ থেকে একটা অপশন বেছে নিন",
  'menu': ["কাজ","ব্যালেন্স","টাকা উত্তোলন","মাই রেফারেল","সাপোর্ট","🎁 গিফট কোড","ভাষা পরিবর্তন","পার্টনার বট","অ্যাডমিন প্যানেল"],
  'back': "🔙 ব্যাক",
  'balance': "💵 আপনার ব্যালেন্স\n━━━━━━━━━━━━━━━━━━━━━━\n💵 ব্যালেন্স: {bal:.2f} BDT\n💸 পেন্ডিং (উইথড্র): {pen:.2f} BDT\n💰 টোটাল ইনকাম: {tot:.2f} টাকা\n━━━━━━━━━━━━━━━━━━━━━━\n✅ সম্পন্ন কাজ: {done} টি\n⏳ রিভিউতে আছে: {rev} টি\n❌ রিজেক্টেড: {rej} টি",
  'wd_menu': "📤 টাকা তোলার মাধ্যম সিলেক্ট করুন:",
  'wd_btns': ["USDT (BEP-20) -> সর্বনিম্ন: 0.25 (-0.05)","বিকাশ -> সর্বনিম্ন: ১১০৳ (-১০)","নগদ -> সর্বনিম্ন: ১১০৳ (-১০)","রকেট -> সর্বনিম্ন: ১১০৳ (-১০)"],
  'no_bal_bkash': "❌ আপনার ব্যালেন্স পর্যাপ্ত নয়। Bkash-এ উইথড্র দিতে কমপক্ষে 110.00 ৳ প্রয়োজন.\nআপনার বর্তমান ব্যালেন্স: {bal:.2f} ৳",
  'no_bal_nagad': "❌ আপনার ব্যালেন্স পর্যাপ্ত নয়। Nagad-এ উইথড্র দিতে কমপক্ষে 110.00 ৳ প্রয়োজন.\nআপনার বর্তমান ব্যালেন্স: {bal:.2f} ৳",
  'no_bal_rocket': "❌ আপনার ব্যালেন্স পর্যাপ্ত নয়। Rocket-এ উইথড্র দিতে কমপক্ষে 110.00 ৳ প্রয়োজন.\nআপনার বর্তমান ব্যালেন্স: {bal:.2f} ৳",
  'referral': "🎁 My Referrals\n👤 মোট রেফার: {cnt}\n😃 মোট রেফারেল আয়: {rinc:.2f} BDT\n🔗 আপনার রেফার লিংক:\n{link}\n\nℹ️ আপনি আপনার প্রতিটি রেফারেলের সম্পূর্ণ করা কাজ থেকে আয়ের 10% কমিশন পাবেন।",
  'admin_menu': ["📝 নতুন কাজ যোগ করুন","📋 কাজ ম্যানেজ করুন","🎁 গিফট কোড তৈরি করুন","💸 উইথড্র রিকোয়েস্ট দেখুন","👥 ইউজার লিস্ট দেখুন","📊 বটের পরিসংখ্যান","📢 ব্রডকাস্ট","✅ পেন্ডিং সাবমিশন","👑 অ্যাডমিন যোগ/বাদ","⚙️ সেটিংস","🛠 মেইনটেনেন্স মোড","🔙 ব্যাক"],
  'support_text': "📞 গ্রাহক সেবা কেন্দ্র\n━━━━━━━━━━━━━━━━━━━━━━\n\nসম্মানিত মেম্বার,\nআপনার যেকোনো সমস্যা বা জিজ্ঞাসার জন্য আমাদের সাপোর্ট টিমের সাথে যোগাযোগ করুন। আমরা দ্রুত সমাধানের চেষ্টা করব।\n⚠️ নোট: অযথা মেসেজ দেওয়া থেকে বিরত থাকুন।\nধন্যবাদ!",
  'support_btn1': "👨‍💻 অ্যাডমিন সাপোর্ট",
  'support_btn2': "📋 সাবমিশন চ্যানেল",
  'partner_text': "😭 আপনার পার্টনার বট প্রোগ্রাম বর্তমানে বন্ধ আছে।\n\n✅ আপনার এক্সেস চালু করতে অ্যাডমিনের সাথে যোগাযোগ করুন⤵️\n➡️ INBOX - @Nexora_X_Support_Bot",
 },
 'en': {
  'welcome': "👋 Assalamu Alaikum!\n\n🌟 Welcome to Nexora X Earn!\n\nEarn money by completing tasks below.\n\n👇 Choose an option",
  'menu': ["Tasks","Balance","Withdraw","My Referral","Support","🎁 Gift Code","Change Language","Partner Bot","Admin Panel"],
  'back': "🔙 Back",
  'balance': "💵 Your Balance\n━━━━━━━━━━━━━━━━━━━━━━\n💵 Balance: {bal:.2f} BDT\n💸 Pending (Withdraw): {pen:.2f} BDT\n💰 Total Income: {tot:.2f} BDT\n━━━━━━━━━━━━━━━━━━━━━━\n✅ Completed: {done}\n⏳ In Review: {rev}\n❌ Rejected: {rej}",
  'wd_menu': "📤 Select Withdraw Method:",
  'wd_btns': ["USDT (BEP-20) -> Min: 0.25 (-0.05)","Bkash -> Min: 110৳ (-10)","Nagad -> Min: 110৳ (-10)","Rocket -> Min: 110৳ (-10)"],
  'no_bal_bkash': "❌ Your balance is not enough. You need at least 110.00 ৳ to withdraw via Bkash.\nYour current balance: {bal:.2f} ৳",
  'no_bal_nagad': "❌ Your balance is not enough. You need at least 110.00 ৳ to withdraw via Nagad.\nYour current balance: {bal:.2f} ৳",
  'no_bal_rocket': "❌ Your balance is not enough. You need at least 110.00 ৳ to withdraw via Rocket.\nYour current balance: {bal:.2f} ৳",
  'referral': "🎁 My Referrals\n👤 Total Refer: {cnt}\n😃 Total Refer Income: {rinc:.2f} BDT\n🔗 Your Refer Link:\n{link}\n\nℹ️ You will get 10% commission from each referral's completed task income.",
  'admin_menu': ["📝 Add New Task","📋 Manage Tasks","🎁 Create Gift Code","💸 Withdraw Requests","👥 User List","📊 Bot Statistics","📢 Broadcast","✅ Pending Submissions","👑 Add/Remove Admin","⚙️ Settings","🛠 Maintenance Mode","🔙 Back"],
  'support_text': "📞 Customer Service Center\n━━━━━━━━━━━━━━━━━━━━━━\n\nDear Member,\nFor any problem or question, contact our support team. We will try to solve it quickly.\n⚠️ Note: Avoid sending unnecessary messages.\nThank you!",
  'support_btn1': "👨‍💻 Admin Support",
  'support_btn2': "📋 Submission Channel",
  'partner_text': "😭 Your Partner Bot program is currently closed.\n\n✅ To activate your access, contact admin⤵️\n➡️ INBOX - @Nexora_X_Support_Bot",
 }
}

def main_menu(uid):
    lang=get_lang(uid); names=T[lang]['menu']
    if uid not in ADMIN_IDS: names=names[:-1]
    kb=[]
    for i in range(0,len(names)-(1 if uid in ADMIN_IDS else 0),2):
        row=[KeyboardButton(names[i])]
        if i+1 < len(names): row.append(KeyboardButton(names[i+1]))
        kb.append(row)
    if uid in ADMIN_IDS: kb.append([KeyboardButton(names[-1])])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def wd_menu_kb(uid):
    lang=get_lang(uid); btns=T[lang]['wd_btns']
    kb=[[KeyboardButton(btns[0])],[KeyboardButton(btns[1])],[KeyboardButton(btns[2])],[KeyboardButton(btns[3])],[KeyboardButton(T[lang]['back'])]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def admin_menu_kb(uid):
    lang=get_lang(uid); names=T[lang]['admin_menu']
    kb=[]
    for i in range(0,len(names),2):
        row=[KeyboardButton(names[i])]
        if i+1 < len(names): row.append(KeyboardButton(names[i+1]))
        kb.append(row)
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; args=context.args
    refer_by=int(args[0]) if args and args[0].isdigit() and int(args[0])!=uid else None
    get_user(uid, refer_by); lang=get_lang(uid)
    await update.message.reply_text(T[lang]['welcome'], reply_markup=main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; text=update.message.text or ""; lang=get_lang(uid)
    con=db(); cur=con.cursor()
    cur.execute("SELECT balance, pending, total_income, done, review, rejected FROM users WHERE id=?", (uid,)); row=cur.fetchone() or (0,0,0,0,0,0)
    bal, pen, tot, done, rev, rej = row
    state=context.user_data.get('state')

    if text in ["🔙 ব্যাক","🔙 Back"]:
        context.user_data['state']=None
        await update.message.reply_text(T[lang]['welcome'], reply_markup=main_menu(uid)); con.close(); return

    if text in ["ব্যালেন্স","Balance"]:
        await update.message.reply_text(T[lang]['balance'].format(bal=bal, pen=pen, tot=tot, done=done, rev=rev, rej=rej)); con.close(); return

    if text in ["কাজ","Tasks"]:
        cur.execute("SELECT id, title, reward FROM tasks"); tasks=cur.fetchall()
        if not tasks: await update.message.reply_text("কোনো কাজ নেই।" if lang=='bn' else "No tasks available."); con.close(); return
        for tid, title, reward in tasks:
            kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ কাজটি করুন / Do Task", callback_data=f"task_{tid}")]])
            await update.message.reply_text(f"📝 {title}\n💰 Reward: {reward} BDT", reply_markup=kb)
        con.close(); return

    if text in ["টাকা উত্তোলন","Withdraw"]:
        await update.message.reply_text(T[lang]['wd_menu'], reply_markup=wd_menu_kb(uid)); con.close(); return

    if text.startswith("USDT"):
        await update.message.reply_text("⚠️ USDT (BEP-20) উত্তোলন বর্তমানে বন্ধ আছে।" if lang=='bn' else "⚠️ USDT (BEP-20) withdrawal is currently closed."); con.close(); return
    if "বিকাশ" in text or "Bkash" in text:
        if bal < 110:
            await update.message.reply_text(T[lang]['no_bal_bkash'].format(bal=bal)); con.close(); return
        context.user_data['state']='wd_bkash'; context.user_data.pop('number',None); context.user_data.pop('await_amount',None)
        await update.message.reply_text("📝 আপনার বিকাশ নাম্বার দিন:" if lang=='bn' else "📝 Enter your Bkash number:"); con.close(); return
    if "নগদ" in text or "Nagad" in text:
        if bal < 110:
            await update.message.reply_text(T[lang]['no_bal_nagad'].format(bal=bal)); con.close(); return
        context.user_data['state']='wd_nagad'; context.user_data.pop('number',None); context.user_data.pop('await_amount',None)
        await update.message.reply_text("📝 আপনার নগদ নাম্বার দিন:" if lang=='bn' else "📝 Enter your Nagad number:"); con.close(); return
    if "রকেট" in text or "Rocket" in text:
        if bal < 110:
            await update.message.reply_text(T[lang]['no_bal_rocket'].format(bal=bal)); con.close(); return
        context.user_data['state']='wd_rocket'; context.user_data.pop('number',None); context.user_data.pop('await_amount',None)
        await update.message.reply_text("📝 আপনার রকেট নাম্বার দিন:" if lang=='bn' else "📝 Enter your Rocket number:"); con.close(); return

    if state and state.startswith("wd_"):
        method=state.split("_")[1]
        if 'number' not in context.user_data:
            context.user_data['number']=text.strip()
            await update.message.reply_text("💰 টাকার পরিমাণ লিখুন:" if lang=='bn' else "💰 Enter amount:")
            context.user_data['await_amount']=True; con.close(); return
        if context.user_data.get('await_amount'):
            try: amt=float(text.strip())
            except: await update.message.reply_text("সঠিক টাকা লিখুন"); con.close(); return
            if amt < 110: await update.message.reply_text("❌ সর্বনিম্ন ১১০৳ তুলতে হবে"); con.close(); return
            if amt > bal: await update.message.reply_text("❌ ব্যালেন্স যথেষ্ট নেই"); con.close(); return
            cur.execute("UPDATE users SET balance=balance-?, pending=pending+? WHERE id=?", (amt, amt, uid))
            cur.execute("INSERT INTO withdraws (user_id, method, number, amount) VALUES (?,?,?,?)", (uid, method, context.user_data['number'], amt)); con.commit()
            await update.message.reply_text(f"✅ #10800 Payment Completed\n🗣 User Name: {update.effective_user.first_name}\n💰 Amount: ${amt*0.009:.4f} USDT\n✅ আপনার উইথড্র রিকোয়েস্ট সফলভাবে গ্রহণ করা হয়েছে : 🔷 বিকাশ/নগদ/রকেট\n🕐 নাম্বার: {context.user_data['number']}\n🔗 পরিমাণ: {amt} টাকা", reply_markup=main_menu(uid))
            for aid in ADMIN_IDS:
                try: await context.bot.send_message(aid, f"🆕 নতুন উইথড্র!\nUser: {uid}\nMethod: {method}\nNumber: {context.user_data['number']}\nAmount: {amt}")
                except: pass
            context.user_data.clear(); con.close(); return

    if text in ["মাই রেফারেল","My Referral"]:
        cur.execute("SELECT COUNT(*) FROM users WHERE refer_by=?", (uid,)); cnt=cur.fetchone()[0]
        cur.execute("SELECT refer_income FROM users WHERE id=?", (uid,)); rinc=cur.fetchone()[0] or 0
        link=f"https://t.me/Nexora_X_Earn_Bot?start={uid}"
        await update.message.reply_text(T[lang]['referral'].format(cnt=cnt, rinc=rinc, link=link)); con.close(); return

    if text in ["সাপোর্ট","Support"]:
        kb=InlineKeyboardMarkup([[InlineKeyboardButton(T[lang]['support_btn1'], url="https://t.me/Nexora_X_Support_Bot")],[InlineKeyboardButton(T[lang]['support_btn2'], url="https://t.me/Nexora_X_Submission")]])
        await update.message.reply_text(T[lang]['support_text'], reply_markup=kb); con.close(); return

    if text in ["🎁 গিফট কোড","🎁 Gift Code"]:
        context.user_data['state']='gift'
        await update.message.reply_text("🎁 গিফট কোড\n\nআপনার গিফট কোডের সিক্রেট কী লিখে পাঠান:" if lang=='bn' else "🎁 Gift Code\n\nSend your gift code secret key:"); con.close(); return
    if state=='gift':
        cur.execute("SELECT amount, used_by FROM giftcodes WHERE code=?", (text.strip(),)); g=cur.fetchone()
        if not g: await update.message.reply_text("❌ ভুল কোড!" if lang=='bn' else "❌ Wrong code!")
        elif str(uid) in g[1].split(","): await update.message.reply_text("❌ এই কোড আগেই ব্যবহার করেছেন!" if lang=='bn' else "❌ You already used this code!")
        else:
            amt=g[0]
            cur.execute("UPDATE users SET balance=balance+?, total_income=total_income+? WHERE id=?", (amt, amt, uid))
            cur.execute("UPDATE giftcodes SET used_by=? WHERE code=?", (g[1]+f",{uid}", text.strip())); con.commit()
            cur.execute("SELECT balance FROM users WHERE id=?", (uid,)); newbal=cur.fetchone()[0]
            await update.message.reply_text(f"🎉 অভিনন্দন!\n\n✨ গিফট কোড সফলভাবে ক্লেইম হয়েছে।\n\n💸 আপনি পেয়েছেন: {amt} টাকা\n💸 বর্তমান ব্যালেন্স: {newbal:.2f} BDT" if lang=='bn' else f"🎉 Congratulations!\n\n✨ Gift code claimed successfully.\n\n💸 You got: {amt} BDT\n💸 Current Balance: {newbal:.2f} BDT")
        context.user_data['state']=None; con.close(); return

    if text in ["ভাষা পরিবর্তন","Change Language"]:
        kb=InlineKeyboardMarkup([[InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn"), InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]])
        await update.message.reply_text("ভাষা সিলেক্ট করুন / Select Language:", reply_markup=kb); con.close(); return

    if text in ["পার্টনার বট","Partner Bot"]:
        await update.message.reply_text(T[lang]['partner_text']); con.close(); return

    if text in ["অ্যাডমিন প্যানেল","Admin Panel"] and uid in ADMIN_IDS:
        await update.message.reply_text("👑 অ্যাডমিন প্যানেল" if lang=='bn' else "👑 Admin Panel", reply_markup=admin_menu_kb(uid)); con.close(); return

    if uid in ADMIN_IDS and text in T[lang]['admin_menu']:
        if "নতুন কাজ" in text or "Add New Task" in text:
            context.user_data['state']='addtask'; await update.message.reply_text("নতুন কাজ লিখুন:\nশিরোনাম | বিবরণ | টাকা | লিংক" if lang=='bn' else "Enter new task:\nTitle | Description | Amount | Link"); con.close(); return
        if "গিফট কোড তৈরি" in text or "Create Gift Code" in text:
            context.user_data['state']='addgift'; await update.message.reply_text("গিফট কোড লিখুন:\nকোড | টাকা\nউদাহরণ: NEXORA50 | 50"); con.close(); return
        if "উইথড্র রিকোয়েস্ট" in text or "Withdraw Requests" in text:
            cur.execute("SELECT id, user_id, method, number, amount FROM withdraws WHERE status='pending'"); rows=cur.fetchall()
            if not rows: await update.message.reply_text("কোনো পেন্ডিং উইথড্র নেই।" if lang=='bn' else "No pending withdraw.")
            for r in rows:
                kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"wd_ok_{r[0]}"), InlineKeyboardButton("❌ Reject", callback_data=f"wd_no_{r[0]}")]])
                await update.message.reply_text(f"ID: {r[0]}\nUser: {r[1]}\nMethod: {r[2]}\nNumber: {r[3]}\nAmount: {r[4]}", reply_markup=kb)
            con.close(); return
        if "কাজ ম্যানেজ" in text or "Manage Tasks" in text:
            cur.execute("SELECT id, title FROM tasks"); rows=cur.fetchall()
            if not rows: await update.message.reply_text("কোনো কাজ নেই।" if lang=='bn' else "No tasks.")
            for r in rows:
                kb=InlineKeyboardMarkup([[InlineKeyboardButton("🗑 ডিলিট", callback_data=f"del_task_{r[0]}")]])
                await update.message.reply_text(f"{r[0]}. {r[1]}", reply_markup=kb)
            con.close(); return
        if "ইউজার লিস্ট" in text or "User List" in text:
            cur.execute("SELECT COUNT(*), SUM(balance) FROM users"); c, tb=cur.fetchone()
            await update.message.reply_text(f"👥 Total Users: {c}\n💰 Total Balance: {tb or 0:.2f}"); con.close(); return
        if "পরিসংখ্যান" in text or "Statistics" in text:
            cur.execute("SELECT COUNT(*) FROM users"); u=cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM withdraws WHERE status='approved'"); w=cur.fetchone()[0]
            cur.execute("SELECT SUM(amount) FROM withdraws WHERE status='approved'"); s=cur.fetchone()[0] or 0
            await update.message.reply_text(f"📊 পরিসংখ্যান\n👥 Users: {u}\n💸 Approved Withdraw: {w}\n💰 Total Paid: {s:.2f} BDT" if lang=='bn' else f"📊 Statistics\n👥 Users: {u}\n💸 Approved Withdraw: {w}\n💰 Total Paid: {s:.2f} BDT"); con.close(); return
        if "ব্রডকাস্ট" in text or "Broadcast" in text:
            context.user_data['state']='broadcast'; await update.message.reply_text("সবাইকে কি মেসেজ পাঠাতে চান? মেসেজটি লিখুন:" if lang=='bn' else "What message do you want to send to all? Write it:"); con.close(); return
        if "পেন্ডিং সাবমিশন" in text or "Pending Submissions" in text:
            cur.execute("SELECT id, user_id, task_id, proof FROM submissions WHERE status='pending'"); rows=cur.fetchall()
            if not rows: await update.message.reply_text("কোনো পেন্ডিং সাবমিশন নেই।" if lang=='bn' else "No pending submissions.")
            for r in rows:
                kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"sub_ok_{r[0]}"), InlineKeyboardButton("❌ Reject", callback_data=f"sub_no_{r[0]}")]])
                await update.message.reply_text(f"Sub ID: {r[0]}\nUser: {r[1]}\nTask: {r[2]}\nProof: {r[3]}", reply_markup=kb)
            con.close(); return
        if "অ্যাডমিন যোগ" in text or "Add/Remove Admin" in text:
            await update.message.reply_text("👑 অ্যাডমিন যোগ করতে কোডে ADMIN_IDS এ ID যোগ করতে হবে। বর্তমান অ্যাডমিন: 9292138695" if lang=='bn' else "👑 To add admin, add ID in ADMIN_IDS in code. Current admin: 9292138695"); con.close(); return
        if "সেটিংস" in text or "Settings" in text:
            await update.message.reply_text("⚙️ সেটিংস\nমিনিমাম উইথড্র: 110৳\nরেফার কমিশন: 10%\nUSDT: বন্ধ\nপার্টনার বট: বন্ধ" if lang=='bn' else "⚙️ Settings\nMinimum Withdraw: 110৳\nRefer Commission: 10%\nUSDT: Closed\nPartner Bot: Closed"); con.close(); return
        if "মেইনটেনেন্স" in text or "Maintenance" in text:
            await update.message.reply_text("🛠 মেইনটেনেন্স মোড - এখনো বন্ধ আছে।" if lang=='bn' else "🛠 Maintenance Mode - Currently off."); con.close(); return
    con.close()

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); uid=q.from_user.id; data=q.data
    con=db(); cur=con.cursor()
    if data in ["lang_bn","lang_en"]:
        lang=data.split("_")[1]
        cur.execute("UPDATE users SET lang=? WHERE id=?", (lang, uid)); con.commit()
        await q.message.reply_text("✅ ভাষা পরিবর্তন হয়েছে!" if lang=='bn' else "✅ Language changed!", reply_markup=main_menu(uid))
    elif data.startswith("task_"):
        tid=int(data.split("_")[1]); cur.execute("SELECT title, desc, reward, link FROM tasks WHERE id=?", (tid,)); t=cur.fetchone()
        if t:
            kb=InlineKeyboardMarkup([[InlineKeyboardButton("📤 সাবমিট করুন", callback_data=f"submit_{tid}")],[InlineKeyboardButton("🔗 লিংক", url=t[3] if t[3] else "https://t.me/Nexora_X_Submission")]])
            await q.message.reply_text(f"📝 {t[0]}\n\n{t[1]}\n\n💰 Reward: {t[2]} BDT", reply_markup=kb)
    elif data.startswith("submit_"):
        tid=int(data.split("_")[1]); context.user_data['state']=f"submit_{tid}"
        await q.message.reply_text("📸 কাজের প্রমাণ (স্ক্রিনশট / লিংক) পাঠান:" if get_lang(uid)=='bn' else "📸 Send proof (Screenshot / Link):")
    elif data.startswith("wd_ok_"):
        wid=int(data.split("_")[2]); cur.execute("SELECT user_id, amount FROM withdraws WHERE id=?", (wid,)); w=cur.fetchone()
        cur.execute("UPDATE withdraws SET status='approved' WHERE id=?", (wid,)); cur.execute("UPDATE users SET pending=pending-? WHERE id=?", (w[1], w[0])); con.commit()
        await q.message.reply_text("✅ Approved"); await context.bot.send_message(w[0], "✅ আপনার উইথড্র Approve হয়েছে!")
    elif data.startswith("wd_no_"):
        wid=int(data.split("_")[2]); cur.execute("SELECT user_id, amount FROM withdraws WHERE id=?", (wid,)); w=cur.fetchone()
        cur.execute("UPDATE withdraws SET status='rejected' WHERE id=?", (wid,)); cur.execute("UPDATE users SET pending=pending-?, balance=balance+?, rejected=rejected+1 WHERE id=?", (w[1], w[1], w[0])); con.commit()
        await q.message.reply_text("❌ Rejected"); await context.bot.send_message(w[0], "❌ আপনার উইথড্র Reject হয়েছে, টাকা ব্যালেন্সে ফেরত গেছে।")
    elif data.startswith("sub_ok_"):
        sid=int(data.split("_")[2]); cur.execute("SELECT user_id, task_id FROM submissions WHERE id=?", (sid,)); s=cur.fetchone()
        cur.execute("SELECT reward FROM tasks WHERE id=?", (s[1],)); rew=cur.fetchone()[0]
        cur.execute("UPDATE submissions SET status='approved' WHERE id=?", (sid,))
        cur.execute("UPDATE users SET balance=balance+?, total_income=total_income+?, done=done+1, review=review-1 WHERE id=?", (rew, rew, s[0]))
        cur.execute("SELECT refer_by FROM users WHERE id=?", (s[0],)); rb=cur.fetchone()[0]
        if rb:
            comm=rew*0.10; cur.execute("UPDATE users SET balance=balance+?, total_income=total_income+?, refer_income=refer_income+? WHERE id=?", (comm, comm, comm, rb))
        con.commit(); await q.message.reply_text("✅ Task Approved"); await context.bot.send_message(s[0], f"✅ আপনার কাজ Approve হয়েছে! +{rew} BDT")
    elif data.startswith("sub_no_"):
        sid=int(data.split("_")[2]); cur.execute("SELECT user_id FROM submissions WHERE id=?", (sid,)); s=cur.fetchone()
        cur.execute("UPDATE submissions SET status='rejected' WHERE id=?", (sid,)); cur.execute("UPDATE users SET rejected=rejected+1, review=review-1 WHERE id=?", (s[0],)); con.commit()
        await q.message.reply_text("❌ Rejected"); await context.bot.send_message(s[0], "❌ আপনার কাজ Reject হয়েছে।")
    elif data.startswith("del_task_"):
        cur.execute("DELETE FROM tasks WHERE id=?", (int(data.split("_")[2]),)); con.commit(); await q.message.reply_text("🗑 কাজ ডিলিট হয়েছে।")
    con.close()

async def handle_extra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; text=update.message.text or ""; state=context.user_data.get('state')
    if not state: return
    con=db(); cur=con.cursor()
    if state.startswith("submit_"):
        tid=int(state.split("_")[1]); cur.execute("INSERT INTO submissions (user_id, task_id, proof) VALUES (?,?,?)", (uid, tid, text)); cur.execute("UPDATE users SET review=review+1 WHERE id=?", (uid,)); con.commit()
        await update.message.reply_text("✅ সাবমিশন জমা হয়েছে, রিভিউতে আছে." if get_lang(uid)=='bn' else "✅ Submission received, in review."); context.user_data['state']=None
    elif state=='addtask' and uid in ADMIN_IDS:
        try:
            title, desc, reward, link=[x.strip() for x in text.split("|")]; cur.execute("INSERT INTO tasks (title, desc, reward, link) VALUES (?,?,?,?)", (title, desc, float(reward), link)); con.commit(); await update.message.reply_text("✅ কাজ যোগ হয়েছে!")
        except: await update.message.reply_text("❌ ফরম্যাট ভুল!")
        context.user_data['state']=None
    elif state=='addgift' and uid in ADMIN_IDS:
        try:
            code, amt=[x.strip() for x in text.split("|")]; cur.execute("INSERT INTO giftcodes (code, amount) VALUES (?,?)", (code, float(amt))); con.commit(); await update.message.reply_text(f"✅ গিফট কোড তৈরি: {code} = {amt} টাকা")
        except: await update.message.reply_text("❌ ফরম্যাট ভুল! কোড | টাকা")
        context.user_data['state']=None
    elif state=='broadcast' and uid in ADMIN_IDS:
        cur.execute("SELECT id FROM users"); users=cur.fetchall(); sent=0
        for (u,) in users:
            try: await context.bot.send_message(u, text); sent+=1
            except: pass
        await update.message.reply_text(f"✅ {sent} জনকে মেসেজ গেছে."); context.user_data['state']=None
    con.close()

def main():
    db(); app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_extra), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg), group=1)
    print("Bot Running - Nexora X Earn"); app.run_polling()
if __name__=="__main__": main()
