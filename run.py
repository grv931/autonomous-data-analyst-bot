import sys
import os
import asyncio
import logging
import argparse
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import settings
from src.bot.handlers import create_bot_application
from src.server.web import web_app
from src.agent.analyst import analyst_agent
from src.engine.dataset import dataset_manager

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("DataAnalystBot")

async def run_web_server():
    """Runs the FastAPI telemetry and public log server."""
    config = uvicorn.Config(
        app=web_app,
        host=settings.server_host,
        port=settings.server_port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    logger.info(f"🚀 Telemetry & Public Log server running at http://{settings.server_host}:{settings.server_port}")
    await server.serve()

async def run_telegram_bot():
    """Runs the Telegram Bot polling loop with automatic recovery from transient conflicts."""
    if not settings.telegram_bot_token:
        logger.warning("⚠️  TELEGRAM_BOT_TOKEN is not set. Telegram polling will not start.")
        logger.warning("👉  To enable Telegram, set TELEGRAM_BOT_TOKEN in .env or run with '--mode cli' for terminal testing.")
        return

    retry_delay = 5
    while True:
        try:
            bot_app = create_bot_application()
            logger.info("🤖 Starting Telegram Bot polling...")
            async with bot_app:
                await bot_app.start()
                await bot_app.updater.start_polling(drop_pending_updates=True)
                retry_delay = 5  # Reset on successful start

                # Continuously monitor updater health
                while bot_app.updater.running:
                    await asyncio.sleep(2)

                logger.warning(f"⚠️ Telegram polling stopped unexpectedly. Retrying in {retry_delay}s...")
        except Exception as e:
            logger.error(f"⚠️ Telegram error: {e}. Retrying in {retry_delay}s...")

        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 30)

async def run_concurrent():
    """Run both Web server and Telegram Bot in the same async event loop."""
    await asyncio.gather(
        run_web_server(),
        run_telegram_bot(),
    )

async def run_cli_mode():
    """Interactive CLI mode for immediate terminal testing without Telegram."""
    print("=" * 60)
    print("🤖 Autonomous Data Analyst Agent — Interactive Terminal Mode")
    print("Type 'exit' to quit, 'summary' to inspect dataset, or ask any query.")
    print("=" * 60)

    chat_id = "cli_user"
    while True:
        try:
            query = input("\n📊 User > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit"]:
                break
            if query.lower() == "summary":
                print(dataset_manager.get_summary_text(chat_id))
                continue

            print("Thinking & computing...")
            resp = await analyst_agent.handle_query(chat_id, query)
            print("\n🤖 Analyst >")
            print(resp.text)
            if resp.chart_path:
                print(f"[Chart saved to: {resp.chart_path}]")
        except (KeyboardInterrupt, EOFError):
            break

def main():
    parser = argparse.ArgumentParser(description="Autonomous Data Analyst Agent")
    parser.add_argument(
        "--mode",
        choices=["all", "bot", "web", "cli"],
        default="all",
        help="Run mode: 'all' (Bot + Web), 'bot' (Telegram only), 'web' (Dashboard only), 'cli' (Terminal test)",
    )
    args = parser.parse_args()

    if args.mode == "cli":
        asyncio.run(run_cli_mode())
    elif args.mode == "web":
        asyncio.run(run_web_server())
    elif args.mode == "bot":
        asyncio.run(run_telegram_bot())
    else:
        asyncio.run(run_concurrent())

if __name__ == "__main__":
    main()
