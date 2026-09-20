import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-ai-study-tutor-secret-key")
    
    # Database
    db_path = BASE_DIR / "ai_tutor.db"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI", f"sqlite:///{db_path}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI Engine Configuration
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "auto").lower()
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()
    OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "nex-agi/nex-n2.5-mini:free").strip()
    # Auto-detect OpenRouter key if pasted into OPENAI_API_KEY
    if not OPENROUTER_API_KEY and OPENAI_API_KEY.startswith("sk-or-"):
        OPENROUTER_API_KEY = OPENAI_API_KEY
    LOCAL_AI_URL = os.environ.get("LOCAL_AI_URL", "http://localhost:11434/api/generate")
    LOCAL_AI_MODEL = os.environ.get("LOCAL_AI_MODEL", "llama3")
    
    # Server
    PORT = int(os.environ.get("PORT", 5000))
    DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
    
    # Uploads
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
