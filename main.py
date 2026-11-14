import os, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

# Render এর জন্য পোর্ট খোলা - এটা মুছবেন না
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")
    def log_message(self, *args):
        pass

def start_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=start_server, daemon=True).start()

WORKS = [
    {"id": "work1", "title": "⭐ Instagram Follow + Like", "price": "15 টাকা", "desc": "আমাদের Instagram পেজ ফলো করে স্ক্রিনশট দিন"},
    {"id": "work2", "title": "⭐ YouTube Subscribe", "price": "20 টাকা", "desc": "আমাদের YouTube চ্যানেল সাবস্ক্রাইব করে স্ক্রিনশট দিন"},
    {"id": "work3", "title": "⭐ Telegram Join + Review", "price": "10 টাকা", "desc": "আমাদের Telegram চ্যানেল জয়েন করে স্ক্রিনশট দিন"},
]

# আপনার চাওয়া Reply Keyboard
def main_keyboard():
    keyboard = [
        ["কাজ", "ব্যালেন্স"],
        ["টাকা উত্তোলন", "মাই রেফারেল"],
        ["সাপোর্ট", "লিডারবোর্ড"],
        ["ভাষা পরিবর্তন", "পার্টনার বট"],
        ["অ্যাডমিন প্যানেল"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "👋 আসসালামু আলাইকুম!\n\n🌟 *Roventrax Bot* এ স্বাগতম!\n\nনিচে থেকে যেকোনো কাজ করে টাকা ইনকাম করতে পারবেন।\n\n👇 নিচ থেকে একটা অপশন বেছে নিন"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, reply_markup=main_keyboard(), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=main_keyboard(), parse_mode="Markdown")

async def show_works(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q:
        await q.answer()
    keyboard = []
    for w in WORKS:
        keyboard.append([InlineKeyboardButton(f"{w['title']} - {w['price']}", callback_data=w['id'])])
    keyboard.append([InlineKeyboardButton("🏠 ফিরে যান", callback_data="home")])
    text = "📋 *আমাদের কাজগুলো:*\n\nনিচের কাজ গুলো করে স্ক্রিনশট পাঠান।"
    if q:
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def work_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    work = next((w for w in WORKS if w['id'] == q.data), None)
    if not work:
        return
    keyboard = [
        [InlineKeyboardButton("✅ কাজটি নিলাম", callback_data=f"take_{work['id']}")],
        [InlineKeyboardButton("🔙 ফিরে যান", callback_data="works")],
    ]
    await q.edit_message_text(f"*{work['title']}*\n\n💰 পেমেন্ট: {work['price']}\n\n📝 কাজ: {work['desc']}\n\nকাজ শেষ করে স্ক্রিনশট পাঠান।", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def take_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    keyboard = [[InlineKeyboardButton("🏠 হোম", callback_data="home")]]
    await q.edit_message_text("✅ *কাজটি আপনি নিয়ে নিয়েছেন!*\n\nকাজ শেষ করে স্ক্রিনশট আমাদের পাঠিয়ে দিন।\n\nআমরা চেক করে আপনার ব্যালেন্সে টাকা যোগ করে দিবো।", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q:
        await q.answer()
        keyboard = [[InlineKeyboardButton("🏠 ফিরে যান", callback_data="home")]]
        await q.edit_message_text("💰 *আপনার ব্যালেন্স: 0 টাকা*\n\nএখনো কোনো টাকা জমা হয়নি। কাজ করে ইনকাম করুন।", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text("💰 *আপনার ব্যালেন্স: 0 টাকা*\n\nএখনো কোনো টাকা জমা হয়নি। কাজ করে ইনকাম করুন।", parse_mode="Markdown")

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q:
        await q.answer()
        keyboard = [[InlineKeyboardButton("🏠 ফিরে যান", callback_data="home")]]
        await q.edit_message_text("🛠 *সাপোর্ট*\n\nকোনো সমস্যা হলে এখানে মেসেজ করুন:\n@RoventraxBot\n\nআমরা দ্রুত রিপ্লাই দিবো।", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text("🛠 *সাপোর্ট*\n\nকোনো সমস্যা হলে এখানে মেসেজ করুন:\n@RoventraxBot\n\nআমরা দ্রুত রিপ্লাই দিবো।", parse_mode="Markdown")

# Reply Keyboard এর বাটনে চাপ দিলে কি হবে
async def button_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "কাজ":
        await show_works(update, context)
    elif text == "ব্যালেন্স":
        await balance(update, context)
    elif text == "টাকা উত্তোলন":
        await update.message.reply_text("💸 *টাকা উত্তোলন*\n\nন্যূনতম উত্তোলন: 100 টাকা\nআপনার ব্যালেন্স: 0 টাকা\n\nউত্তোলন করতে আপনার বিকাশ / নগদ নম্বর পাঠান।", parse_mode="Markdown")
    elif text == "মাই রেফারেল":
        user_id = update.message.from_user.id
        await update.message.reply_text(f"👥 *মাই রেফারেল*\n\nআপনার রেফারেল লিংক:\nhttps://t.me/RoventraxBot?start={user_id}\n\nপ্রতি রেফারে পাবেন 5 টাকা।", parse_mode="Markdown")
    elif text == "সাপোর্ট":
        await support(update, context)
    elif text == "লিডারবোর্ড":
        await update.message.reply_text("🏆 *লিডারবোর্ড*\n\n1. @user1 - 500 টাকা\n2. @user2 - 350 টাকা\n3. @user3 - 200 টাকা\n\nআপনি এখনো লিস্টে নেই, কাজ করুন!", parse_mode="Markdown")
    elif text == "ভাষা পরিবর্তন":
        await update.message.reply_text("🌐 *ভাষা পরিবর্তন*\n\nবাংলা - চালু আছে ✅\nEnglish - শীঘ্রই আসছে", parse_mode="Markdown")
    elif text == "পার্টনার বট":
        await update.message.reply_text("🤝 *পার্টনার বট*\n\nআমাদের পার্টনার বট:\n@PartnerBot\n\nওখানে আরও বেশি কাজ পাবেন।", parse_mode="Markdown")
    elif text == "অ্যাডমিন প্যানেল":
        await update.message.reply_text("🔐 *অ্যাডমিন প্যানেল*\n\nএই অপশন শুধু অ্যাডমিনদের জন্য।\nআপনি অ্যাডমিন না হলে এটা ব্যবহার করতে পারবেন না।", parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.data == "home":
        await start(update, context)
    elif q.data == "works":
        await show_works(update, context)
    elif q.data == "balance":
        await balance(update, context)
    elif q.data == "support":
        await support(update, context)
    elif q.data.startswith("take_"):
        await take_work(update, context)
    elif q.data in ["work1", "work2", "work3"]:
        await work_detail(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_reply))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
