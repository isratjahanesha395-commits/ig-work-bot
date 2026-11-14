import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

WORKS = [
    {"id": "work1", "title": "📸 Instagram Follow + Like", "price": "15 টাকা", "desc": "আমাদের Instagram পেজ ফলো করে স্ক্রিনশট দিন।"},
    {"id": "work2", "title": "▶️ YouTube Subscribe", "price": "20 টাকা", "desc": "আমাদের YouTube চ্যানেল সাবস্ক্রাইব করে স্ক্রিনশট দিন।"},
    {"id": "work3", "title": "⭐ Telegram Join + Review", "price": "10 টাকা", "desc": "আমাদের Telegram চ্যানেল জয়েন করে স্ক্রিনশট দিন।"},
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💼 কাজ দেখুন", callback_data="works")],
        [InlineKeyboardButton("💰 আমার ব্যালেন্স", callback_data="balance")],
        [InlineKeyboardButton("📞 সাপোর্ট", callback_data="support")],
    ]
    text = "👋 আসসালামু আলাইকুম!\n\n🌟 *Roventra X Bot* এ স্বাগতম!\n\nএখানে ছোট ছোট কাজ করে টাকা ইনকাম করতে পারবেন।\n\nনিচে থেকে একটা অপশন বেছে নিন:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_works(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    keyboard = []
    for w in WORKS:
        keyboard.append([InlineKeyboardButton(f"{w['title']} - {w['price']}", callback_data=w['id'])])
    keyboard.append([InlineKeyboardButton("⬅️ ফিরে যান", callback_data="home")])
    await q.edit_message_text("💼 *আজকের কাজগুলো:*\n\nএকটা কাজে ক্লিক করে ডিটেইলস দেখুন:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def work_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    work = next((w for w in WORKS if w['id'] == q.data), None)
    if not work:
        return
    keyboard = [
        [InlineKeyboardButton("✅ কাজটা নিলাম", callback_data=f"take_{work['id']}")],
        [InlineKeyboardButton("⬅️ ফিরে যান", callback_data="works")],
    ]
    await q.edit_message_text(f"*{work['title']}*\n\n💰 পেমেন্ট: {work['price']}\n\n📝 কাজ: {work['desc']}\n\nকাজ শেষ করে স্ক্রিনশট সাপোর্টে পাঠান।", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def take_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    keyboard = [[InlineKeyboardButton("⬅️ হোম", callback_data="home")]]
    await q.edit_message_text("✅ *কাজটা আপনি নিয়ে নিয়েছেন!*\n\nকাজ শেষ করে স্ক্রিনশটটা আমাদের সাপোর্টে পাঠিয়ে দিন।\n\nআমরা চেক করে আপনার ব্যালেন্সে টাকা যোগ করে দিবো।", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    keyboard = [[InlineKeyboardButton("⬅️ ফিরে যান", callback_data="home")]]
    await q.edit_message_text("💰 *আপনার ব্যালেন্স: 0 টাকা*\n\nকাজ শেষ করলে এখানে টাকা জমা হবে।", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    keyboard = [[InlineKeyboardButton("⬅️ ফিরে যান", callback_data="home")]]
    await q.edit_message_text("📞 *সাপোর্ট*\n\nকোনো সমস্যা হলে এখানে মেসেজ করুন:\n@RoventraXBot\n\nআমরা দ্রুত রিপ্লাই দিবো।", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

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
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
