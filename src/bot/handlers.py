import io
import logging
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from config import settings
from src.agent.analyst import analyst_agent
from src.engine.dataset import dataset_manager
from src.bot.formatter import format_welcome_message, format_help_message

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    bot_info = await context.bot.get_me()
    welcome = format_welcome_message(bot_info.username or "DataAnalystBot")
    await update.message.reply_text(welcome, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_help_message(), parse_mode="Markdown")

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    summary = dataset_manager.get_summary_text(chat_id)
    await update.message.reply_text(summary, parse_mode="Markdown")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    dataset_manager.clear(chat_id)
    analyst_agent.conversations.pop(chat_id, None)
    await update.message.reply_text("🧹 Session cleared. Conversation history and active dataset reset.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dataset uploads (CSV, Excel, JSON, Parquet)."""
    chat_id = update.effective_chat.id
    doc = update.message.document

    if not doc:
        return

    filename = doc.file_name or "uploaded_dataset"
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    status_msg = await update.message.reply_text(f"📥 Downloading `{filename}`...", parse_mode="Markdown")

    try:
        tg_file = await doc.get_file()
        file_bytes = await tg_file.download_as_bytearray()

        df, _ = dataset_manager.load_from_bytes(chat_id, filename, bytes(file_bytes))
        summary = dataset_manager.get_summary_text(chat_id)

        rows, cols = df.shape
        await status_msg.edit_text(
            f"✅ **Loaded `{filename}` successfully!**\n\n"
            f"• **Dimensions**: {rows:,} rows × {cols} columns\n"
            f"• **Columns**: {', '.join([f'`{c}`' for c in list(df.columns)[:8]])}"
            f"{'...' if cols > 8 else ''}\n\n"
            f"💡 *Ask me any question about this data, request charts, or type `/summary`!*",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception("Failed to load uploaded dataset")
        await status_msg.edit_text(f"❌ Failed to process `{filename}`: {str(e)}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process incoming text query."""
    chat_id = update.effective_chat.id
    user_text = update.message.text

    if not user_text:
        return

    # Indicate activity
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # Process via autonomous agent
    response = await analyst_agent.handle_query(chat_id, user_text)

    # Send text or JSON reply
    if response.is_json:
        # Grader mode: return raw JSON string exactly
        await update.message.reply_text(response.text)
    else:
        # Conversational mode
        try:
            await update.message.reply_text(response.text, parse_mode="Markdown")
        except Exception:
            # Fallback if markdown contains unmatched special characters
            await update.message.reply_text(response.text)

    # If chart was generated, send it as photo
    if response.chart_bytes:
        try:
            photo_io = io.BytesIO(response.chart_bytes)
            photo_io.name = "analysis_chart.png"
            await update.message.reply_photo(
                photo=photo_io,
                caption="📈 Visual Analysis Result",
            )
        except Exception as e:
            logger.error(f"Failed to send chart photo: {e}")

def create_bot_application() -> Application:
    """Build and configure the Telegram application."""
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is not configured in settings or environment!")

    app = Application.builder().token(settings.telegram_bot_token).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("clear", clear_command))

    # Document upload
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app
