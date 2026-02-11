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

MEMORY_FILE = "memory.json"

# Load memory
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)
else:
    memory = {}

# -----------------------------
# Helper Functions
# -----------------------------
def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)

async def call_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

# -----------------------------
# Command Handlers
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐺 Direwolf online! Chat with me freely or use /setproduct to save your product."
    )

async def set_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /setproduct <your product description>")
        return
    product_info = " ".join(context.args)
    memory[user_id] = {"product": product_info}
    save_memory()
    await update.message.reply_text(f"Product saved: {product_info}")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in memory:
        memory.pop(user_id)
        save_memory()
    await update.message.reply_text("Memory cleared. Use /setproduct to set a new product.")

# -----------------------------
# Free Chat Handler
# -----------------------------
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return  # ignore non-text messages

    user_id = str(update.message.from_user.id)
    user_message = update.message.text

    # Include product info if set
    product_info = memory.get(user_id, {}).get("product", "")
    if product_info:
        prompt = f"Act as a tactical, calm, persuasive Web3 sales AI named Direwolf. Product: {product_info}. Reply to this user tactically: {user_message}"
    else:
        prompt = f"Act as a tactical, calm, persuasive Web3 sales AI named Direwolf. Reply to this user tactically: {user_message}"

    reply = await call_openai(prompt)
    await update.message.reply_text(reply)

# -----------------------------
# Main Application
# -----------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setproduct", set_product))
    app.add_handler(CommandHandler("reset", reset))

    # Free chat handler for all text messages
    # Important: filters.TEXT catches all text messages, even in groups if mentioned
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat))

    print("🐺 Direwolf is online and polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
