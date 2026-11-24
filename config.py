import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
# Always load .env relative to project root
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings(BaseModel):
    # Telegram Bot Settings
    telegram_bot_token: str = Field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    
    # AI / LLM Provider Settings
    llm_provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini"))  # gemini, openai, aipipe, ollama
    
    # Google Gemini Settings
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
    
    # OpenAI Settings
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_base_url: str = Field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    
    # TDS / AI Pipe Support
    aipipe_token: str = Field(default_factory=lambda: os.getenv("AIPIPE_TOKEN", ""))
    aipipe_model: str = Field(default_factory=lambda: os.getenv("AIPIPE_MODEL", "gpt-5-mini"))
    
    # Web Dashboard & Public Log Server
    server_host: str = Field(default_factory=lambda: os.getenv("SERVER_HOST", "0.0.0.0"))
    server_port: int = Field(default_factory=lambda: int(os.getenv("PORT", os.getenv("SERVER_PORT", "8000"))))
    public_base_url: str = Field(default_factory=lambda: os.getenv("PUBLIC_BASE_URL", "http://localhost:8000"))
    
    # Storage & Paths
    log_file: str = Field(default_factory=lambda: os.getenv("LOG_FILE", str(BASE_DIR / "run.jsonl")))
    data_dir: Path = Field(default_factory=lambda: BASE_DIR / "data")
    charts_dir: Path = Field(default_factory=lambda: BASE_DIR / "charts")
    
    # Sandbox limits
    code_exec_timeout: int = Field(default_factory=lambda: int(os.getenv("CODE_EXEC_TIMEOUT", "15")))
    max_history_turns: int = Field(default_factory=lambda: int(os.getenv("MAX_HISTORY_TURNS", "10")))

settings = Settings()
