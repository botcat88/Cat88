import json
import os
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 🛠 Cấu hình
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 6077546091
USER_DATA_FILE = "users.json"
START_MONEY = 10_000_000
BET_AMOUNT = 10_000_000

# 🔄 Lưu / Tải người dùng
def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f)

def get_or_create_user(user_id):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"money": 0, "history": []}
        save_users(users)
    return users[uid]

def update_user_full(user_id, money, history):
    users = load_users()
    users[str(user_id)] = {"money": money, "history": history[-5:]}
    save_users(users)

def update_user(user_id, money):
    user = get_or_create_user(user_id)
    update_user_full(user_id, money, user.get("history", []))

# 🎲 Xử lý kết quả xúc xắc
def roll_dice():
    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    chan_le = "chan" if total % 2 == 0 else "le"
    tai_xiu = "tai" if total >= 11 else "xiu"
    return dice, total, chan_le, tai_xiu

# 🧠 Xử lý cược
async def process_bet(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str, amount: int):
    user_id = update.message.from_user.id
    user = get_or_create_user(user_id)

    if user["money"] < amount:
        await update.message.reply_text("❌ Bạn không đủ tiền để chơi!")
        return

    dice, total, chan_le, tai_xiu = roll_dice()
    result_msg = f"♻ Kết quả 🎲 : {dice}\n"
    symbol = ("⚫" if tai_xiu == "tai" else "⚪") + ("🟢" if chan_le == "chan" else "🔴")

    if choice == tai_xiu or choice == chan_le:
        reward = int(amount * 1.9)
        user["money"] += reward
        result_msg += f"✅ Trúng cược! Nhận {reward:,}đ\n"
    else:
        user["money"] -= amount
        result_msg += f"💥 Thua! Mất {amount:,}đ\n"

    result_msg += f"💰 Số dư của bạn: {user['money']:,}đ\n"
    user["history"].append(symbol)
    update_user_full(user_id, user["money"], user["history"])
    result_msg += "📈 Cầu gần nhất: " + " ".join(user["history"][::-1])
    await update.message.reply_text(result_msg)

# ▶️ /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲 Bot Chẵn Lẻ Tài Xỉu!\n"
        "Gõ /dangky để nhận tiền miễn phí nếu chưa có tài khoản.\n"
        "Đặt cược: T/X/C/L [số tiền]\n"
        "Hoặc dùng lệnh nhanh: /cltx [T/X/C/L] [số tiền]\n"
        "Xem số dư: /sodu | Xem top: /top"
    )

# 🆕 /dangky
async def dangky(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_or_create_user(user_id)
    if user["money"] == 0:
        user["money"] += START_MONEY
        update_user_full(user_id, user["money"], user.get("history", []))
        await update.message.reply_text(
            "Chào mừng đến với Meow Meow 88! Bạn đã được tặng 10,000,000 VNĐ khởi nghiệp.\n"
            "Chơi ngay bằng cách gửi T/X/C/L [số tiền] hoặc dùng lệnh /cltx"
        )
    else:
        await update.message.reply_text("❗ Bạn đã đăng ký hoặc vẫn còn tiền!")

# 💰 /sodu
async def sodu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_or_create_user(update.message.from_user.id)
    await update.message.reply_text(f"💰 Số dư: {user['money']:,}đ")

# 🏆 /top
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    sorted_users = sorted(users.items(), key=lambda x: x[1]["money"], reverse=True)
    msg = "🏆 TOP 5 NGƯỜI GIÀU NHẤT:\n"
    for i, (uid, data) in enumerate(sorted_users[:5], 1):
        msg += f"{i}. ID:{uid} - {data['money']:,}đ\n"
    await update.message.reply_text(msg)

# 🎯 /cltx [T/X/C/L] [số tiền]
async def cltx_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("❗ Cú pháp: /cltx [T/X/C/L] [số tiền]")
        return

    choice = context.args[0].lower()
    try:
        amount = int(context.args[1])
    except:
        await update.message.reply_text("❗ Số tiền phải là số!")
        return

    if choice not in ["t", "x", "c", "l"]:
        await update.message.reply_text("❗ Chọn 1 trong: T/X/C/L")
        return

    mapping = {"t": "tai", "x": "xiu", "c": "chan", "l": "le"}
    await process_bet(update, context, mapping[choice], amount)

# 🎮 Gõ T/X/C/L [số tiền]
async def handle_text_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.strip().lower().split()
        if len(parts) != 2:
            return

        choice, amount = parts[0], int(parts[1])
        mapping = {"t": "tai", "x": "xiu", "c": "chan", "l": "le"}
        if choice in mapping:
            await process_bet(update, context, mapping[choice], amount)
    except:
        await update.message.reply_text("❗ Cú pháp: T/X/C/L [số tiền]")

# 🚀 Khởi động bot
app = ApplicationBuilder().token(TOKEN).build()

# ⌨️ Command
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("dangky", dangky))
app.add_handler(CommandHandler("sodu", sodu))
app.add_handler(CommandHandler("top", top))
app.add_handler(CommandHandler("cltx", cltx_command))

# ✉️ Tin nhắn cược
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_choice))

if __name__ == "__main__":
    app.run_polling()
