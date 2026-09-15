import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ==================================================
# CONFIG
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured.")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# In-memory settings
SOURCE_CHAT_ID = None
DESTINATION_CHAT_ID = None

# ==================================================
# ADMIN CHECK
# ==================================================

def is_admin(user_id):
    return user_id == ADMIN_ID


async def check_admin(update):
    user = update.effective_user

    if not user or not is_admin(user.id):
        if update.message:
            await update.message.reply_text(
                "❌ এই কমান্ডটি শুধুমাত্র Bot Admin ব্যবহার করতে পারবেন।"
            )
        return False

    return True


# ==================================================
# START
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "📋 Source",
                callback_data="show_source"
            ),
            InlineKeyboardButton(
                "🎯 Destination",
                callback_data="show_destination"
            )
        ],
        [
            InlineKeyboardButton(
                "🔗 Join New Group",
                callback_data="join_group"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ Check My Join",
                callback_data="check_join"
            )
        ],
    ]

    await update.message.reply_text(
        "🤖 *Telegram Migration Assistant*\n\n"
        "পুরোনো Group থেকে নতুন Group-এ যাওয়ার "
        "জন্য নিচের বাটন ব্যবহার করুন।\n\n"
        "⚠️ সদস্যকে নিজে Join করতে হবে।\n"
        "বট কাউকে জোর করে Group-এ Add করবে না।",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# SOURCE COMMAND
# ==================================================

async def source(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global SOURCE_CHAT_ID

    if not await check_admin(update):
        return

    if not context.args:
        await update.message.reply_text(
            "ব্যবহার:\n"
            "/source -1001234567890"
        )
        return

    SOURCE_CHAT_ID = context.args[0]

    await update.message.reply_text(
        f"✅ Source Group সেট হয়েছে:\n{SOURCE_CHAT_ID}"
    )


# ==================================================
# DESTINATION COMMAND
# ==================================================

async def destination(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global DESTINATION_CHAT_ID

    if not await check_admin(update):
        return

    if not context.args:
        await update.message.reply_text(
            "ব্যবহার:\n"
            "/destination -1009876543210"
        )
        return

    DESTINATION_CHAT_ID = context.args[0]

    await update.message.reply_text(
        f"✅ Destination Group সেট হয়েছে:\n"
        f"{DESTINATION_CHAT_ID}"
    )


# ==================================================
# STATUS
# ==================================================

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await check_admin(update):
        return

    await update.message.reply_text(
        "📊 Migration Settings\n\n"
        f"📋 Source:\n{SOURCE_CHAT_ID or 'Not set'}\n\n"
        f"🎯 Destination:\n"
        f"{DESTINATION_CHAT_ID or 'Not set'}"
    )


# ==================================================
# CREATE INVITE LINK
# ==================================================

async def create_invite_link(bot):

    if not DESTINATION_CHAT_ID:
        return None

    try:
        invite = await bot.create_chat_invite_link(
            chat_id=DESTINATION_CHAT_ID,
            name="Member Migration"
        )

        return invite.invite_link

    except Exception:
        logging.exception("Could not create invite link")
        return None


# ==================================================
# JOIN BUTTON
# ==================================================

async def join_group(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if not DESTINATION_CHAT_ID:
        await query.message.reply_text(
            "❌ Destination Group এখনো সেট করা হয়নি।"
        )
        return

    invite_link = await create_invite_link(context.bot)

    if not invite_link:
        await query.message.reply_text(
            "❌ Invite Link তৈরি করা যায়নি।\n\n"
            "নিশ্চিত করুন Bot-কে Destination Group-এ "
            "প্রয়োজনীয় Admin permission দেওয়া হয়েছে।"
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Join New Group",
                url=invite_link
            )
        ],
        [
            InlineKeyboardButton(
                "✅ Check My Join",
                callback_data="check_join"
            )
        ]
    ]

    await query.message.reply_text(
        "🎯 *নতুন Group-এ Join করুন*\n\n"
        "নিচের `Join New Group` বাটনে চাপুন "
        "এবং নতুন Group-এ Join করুন।\n\n"
        "Join করার পর `Check My Join` চাপুন।",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# CHECK JOIN
# ==================================================

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    if not DESTINATION_CHAT_ID:
        await query.message.reply_text(
            "❌ Destination Group সেট করা হয়নি।"
        )
        return

    try:

        member = await context.bot.get_chat_member(
            chat_id=DESTINATION_CHAT_ID,
            user_id=user.id
        )

        status = member.status

        if status in ["member", "administrator", "creator"]:

            await query.message.reply_text(
                "🎉 *Join Verified!*\n\n"
                "আপনি সফলভাবে নতুন Group-এ Join করেছেন।",
                parse_mode="Markdown"
            )

        else:

            await query.message.reply_text(
                "❌ এখনো Join করা হয়নি।\n\n"
                "আগে `Join New Group` বাটনে চাপুন।"
            )

    except Exception:

        await query.message.reply_text(
            "❌ Join status যাচাই করা যায়নি।\n\n"
            "নিশ্চিত করুন Bot-টি Destination Group-এ "
            "আছে এবং প্রয়োজনীয় permission রয়েছে।"
        )


# ==================================================
# BUTTON HANDLER
# ==================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if query.data == "join_group":
        await join_group(update, context)

    elif query.data == "check_join":
        await check_join(update, context)

    elif query.data == "show_source":

        await query.answer()

        await query.message.reply_text(
            f"📋 Source Group:\n"
            f"{SOURCE_CHAT_ID or 'Not configured'}"
        )

    elif query.data == "show_destination":

        await query.answer()

        await query.message.reply_text(
            f"🎯 Destination Group:\n"
            f"{DESTINATION_CHAT_ID or 'Not configured'}"
        )


# ==================================================
# MIGRATE COMMAND
# ==================================================

async def migrate(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await check_admin(update):
        return

    if not SOURCE_CHAT_ID or not DESTINATION_CHAT_ID:

        await update.message.reply_text(
            "❌ আগে Source এবং Destination সেট করুন।\n\n"
            "/source -1001111111111\n"
            "/destination -1002222222222"
        )
        return

    invite_link = await create_invite_link(context.bot)

    if not invite_link:

        await update.message.reply_text(
            "❌ Destination Invite Link তৈরি করা যায়নি."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Join New Group",
                url=invite_link
            )
        ]
    ]

    await update.message.reply_text(
        "📢 *Group Migration*\n\n"
        "আমাদের নতুন Group-এ চলে আসুন।\n\n"
        "নিচের বাটনে চাপ দিয়ে নিজে Join করুন।",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# HELP
# ==================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📚 Commands\n\n"
        "/start - Bot Start\n"
        "/source CHAT_ID - Source Group\n"
        "/destination CHAT_ID - Destination Group\n"
        "/status - Settings\n"
        "/migrate - Migration Link\n"
        "/help - Help"
    )


# ==================================================
# ERROR HANDLER
# ==================================================

async def error_handler(update, context):

    logging.error(
        "Bot error:",
        exc_info=context.error
    )


# ==================================================
# MAIN
# ==================================================

def main():

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("source", source))
    app.add_handler(CommandHandler("destination", destination))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("migrate", migrate))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_error_handler(error_handler)

    print("🤖 Migration Bot is running...")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
