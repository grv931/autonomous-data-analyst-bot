import html
import re

def escape_markdown(text: str) -> str:
    """Escapes markdown characters for safe Telegram Markdown rendering if needed."""
    return text

def format_welcome_message(bot_username: str = "DataAnalystBot") -> str:
    return (
        f"👋 **Welcome to the Autonomous Data Analyst Agent!**\n\n"
        f"I am your AI-powered data scientist inside Telegram. Here is what I can do for you:\n\n"
        f"📊 **Data Ingestion**: Send me any **CSV, Excel (.xlsx), Parquet, or JSON** file.\n"
        f"🔍 **Exploratory Data Analysis**: Ask for distributions, correlations, summaries, or outliers.\n"
        f"📈 **Instant Visualizations**: Ask me to plot histograms, heatmaps, bar charts, or trends.\n"
        f"🧮 **Statistical Computing**: Run t-tests, regressions, aggregations, and math live.\n"
        f"🤖 **Automated Grading & API Mode**: Supports strict JSON replies with live public `run.jsonl` audit logging.\n\n"
        f"**Commands:**\n"
        f"• `/summary` - View active dataset structure and summary\n"
        f"• `/clear` - Reset dataset and conversation history\n"
        f"• `/help` - Usage tips and prompt examples\n\n"
        f"Try uploading a dataset or asking me a question directly!"
    )

def format_help_message() -> str:
    return (
        f"📖 **Data Analyst Bot — Help & Capabilities**\n\n"
        f"1️⃣ **Analyzing Files**:\n"
        f"Drag & drop or send a CSV or Excel file. Once uploaded, ask:\n"
        f"- *'Show correlation between marketing spend and revenue'*\n"
        f"- *'Plot a boxplot of salaries by department'*\n"
        f"- *'Which region had the highest average order value?'*\n\n"
        f"2️⃣ **Strict Evaluation / Grading Mode**:\n"
        f"If you send a query like:\n"
        f"```text\nWhat is 15% of 200? Reply with ONLY this JSON: {{\"answer\": <number>, \"log_url\": \"...\"}}\n```\n"
        f"The bot will respond with exactly one machine-readable JSON object matching that schema.\n\n"
        f"3️⃣ **Audit & Public Logs**:\n"
        f"Every query is logged to `run.jsonl`. Check your web dashboard for live monitoring!"
    )
