import json
import os
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 🛠 Cấu hình
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 6077546091  # 🔐 Thay bằng Telegram user ID của bạn
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

# ▶️ /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲 Bot Chẵn Lẻ Tài Xỉu!\n"
        "Dùng /dangky để nhận tiền miễn phí nếu chưa có tài khoản.\n"
        "Gõ T (Tài), X (Xỉu), C (Chẵn), L (Lẻ) để chơi.\n"
        "Xem số dư: /sodu\nXem top: /top"
    )

# 🆕 /dangky
async def dangky(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_or_create_user(user_id)
    if user["money"] == 0:
        user["money"] += 10_000_000
        save_data()
        await update.message.reply_text(
            "Chào mừng bạn đến với Meow Meow 88!\n"
            "**Chức năng:**\n"
            "- **Tai xiu:**\n"
            " - Đặt cược: `T/X/C/L sotien` (Tai, Xiu, Chan, Le)\n\n"
            "Bạn đã được tặng 10,000,000 VNĐ làm vốn khởi nghiệp. Chúc bạn may mắn!"
        )
    else:
        await update.message.reply_text("Bạn đã đăng ký rồi hoặc vẫn còn tiền!")

# 🎰 Chơi game
async def play_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_or_create_user(user_id)

    if user["money"] < BET_AMOUNT:
        await update.message.reply_text("❌ Bạn không đủ tiền để chơi!")
        return

    choice = update.message.text[1:].lower()
    dice, total, chan_le, tai_xiu = roll_dice()

    result_msg = f"♻ Kết quả 🎲 : {dice}\n"
    win = False
    symbol = "⚫" if tai_xiu == "tai" else "⚪"
    symbol += "🟢" if chan_le == "chan" else "🔴"

    if choice == tai_xiu or choice == chan_le:
        reward = int(BET_AMOUNT * 1.9)
        user["money"] += reward
        result_msg += f"♻ Trúng cược! Nhận được {reward:,}đ\n"
        win = True
    else:
        user["money"] -= BET_AMOUNT
        result_msg += f"💥 Thua! Mất {BET_AMOUNT:,}đ\n"

    result_msg += f"💰 Số dư của bạn: {user['money']:,}đ\n"
    user["history"].append(symbol)
    update_user_full(user_id, user["money"], user["history"])
    result_msg += "Cầu gần nhất là " + " ".join(user["history"][-5:])
    await update.message.reply_text(result_msg)

# 💰 /sodu
async def sodu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_or_create_user(update.message.from_user.id)
    await update.message.reply_text(f"💰 Số dư của bạn: {user['money']:,}đ")

# 🏆 /top
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    sorted_users = sorted(users.items(), key=lambda x: x[1]["money"], reverse=True)
    msg = "🏆 TOP 5 NGƯỜI GIÀU NHẤT:\n"
    for i, (uid, data) in enumerate(sorted_users[:5], 1):
        msg += f"{i}. ID:{uid} - {data['money']:,}đ\n"
    await update.message.reply_text(msg)

# 🔡 Nhập T/X/C/L
async def handle_text_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    mapping = {"t": "tai", "x": "xiu", "c": "chan", "l": "le"}
    if text in mapping:
        update.message.text = "/" + mapping[text]
        await play_game(update, context)
    else:
        await update.message.reply_text("❓ Nhập 1 ký tự: T (Tài), X (Xỉu), C (Chẵn), L (Lẻ).")

# 🔑 /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        await update.message.reply_text("🔐 Bạn là admin.")
    else:
        await update.message.reply_text("❌ Bạn không có quyền admin.")

# 💵 /naptien ID SOTIEN
async def naptien(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bạn không phải admin.")
        return

    try:
        args = context.args
        target_id = str(args[0])
        amount = int(args[1])
        users = load_users()
        if target_id not in users:
            await update.message.reply_text("❌ Không tìm thấy người dùng.")
            return
        users[target_id]["money"] += amount
        save_users(users)
        await update.message.reply_text(f"✅ Đã nạp {amount:,}đ cho ID: {target_id}")
    except:
        await update.message.reply_text("❗ Dùng đúng cú pháp: /naptien ID SOTIEN")

# 🚀 Khởi động bot
app = ApplicationBuilder().token(TOKEN).build()

# ⌨️ Command
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("dangky", dangky))
app.add_handler(CommandHandler("sodu", sodu))
app.add_handler(CommandHandler("top", top))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("naptien", naptien))

for cmd in ["chan", "le", "tai", "xiu"]:
    app.add_handler(CommandHandler(cmd, play_game))

# ✉️ Text thường (T/X/C/L)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_choice))

if __name__ == "__main__":
    app.run_polling()
