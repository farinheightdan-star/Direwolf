import os
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import openai

# -----------------------------
# Setup
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Memory file
MEMORY_FILE = "memory.json"

# Load memory or initialize
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)
else:
    memory = {}

# -----------------------------
# Helper functions
# -----------------------------
def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)

async def call_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=250
    )
    return response.choices[0].message.content.strip()

# -----------------------------
# Command Handlers
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐺 Direwolf online! Use /setproduct to save your product.")

async def set_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /setproduct <your product description>")
        return
    product_info = " ".join(context.args)
    memory[user_id] = {"product": product_info}
    save_memory()
    await update.message.reply_text(f"Product saved: {product_info}")

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id not in memory:
        await update.message.reply_text("No product set. Use /setproduct first.")
        return
    product_info = memory[user_id]["product"]
    prompt = f"Give a smart, tactical analysis for pitching this product: {product_info}"
    result = await call_openai(prompt)
    await update.message.reply_text(result)

async def pitch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id not in memory:
        await update.message.reply_text("No product set. Use /setproduct first.")
        return
    product_info = memory[user_id]["product"]
    prompt = f"Write a persuasive cold DM pitch for this product: {product_info}"
    result = await call_openai(prompt)
    await update.message.reply_text(result)

async def objection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /objection <objection text>")
        return
    objection_text = " ".join(context.args)
    user_id = str(update.message.from_user.id)
    product_info = memory.get(user_id, {}).get("product", "your product")
    prompt = f"How to answer this objection tactically for the product '{product_info}': {objection_text}"
    result = await call_openai(prompt)
    await update.message.reply_text(result)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in memory:
        memory.pop(user_id)
        save_memory()
    await update.message.reply_text("Memory cleared. You can set a new product with /setproduct.")

# -----------------------------
# Default message handler
# -----------------------------
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unknown command. Try /start, /setproduct, /analyze, /pitch, /objection, /reset")

# -----------------------------
# Main Application
# -----------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setproduct", set_product))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("pitch", pitch))
    app.add_handler(CommandHandler("objection", objection))
    app.add_handler(CommandHandler("reset", reset))

    # Unknown commands
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Start polling
    print("🐺 Direwolf is online and polling...")
    app.run_polling()

# -----------------------------
if __name__ == "__main__":
    main()
