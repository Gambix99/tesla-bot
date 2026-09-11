"""
Configurazione centrale del bot.
Tutti i valori sensibili vengono letti dal file .env (vedi .env.example).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # dove arrivano le notifiche automatiche

# --- Email ---
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT") or "465")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM") or SMTP_USER
EMAIL_TO = os.getenv("EMAIL_TO")

# --- Controllo periodico ---
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "1800"))  # 30 minuti

# --- Storage ---
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
SEEN_VINS_FILE = os.path.join(DATA_DIR, "seen_vins_model3_rwd.json")

# --- Filtro "trazione posteriore" ---
# La Model 3 in Europa ha 3 varianti: base (RWD), Long Range (AWD) e
# Performance (AWD). Escludendo Long Range/Performance/AWD resta solo
# la versione a trazione posteriore, senza dover indovinare il codice
# TRIM esatto usato internamente da Tesla (che può cambiare nel tempo).
EXCLUDE_TRIM_KEYWORDS = [
    "long range",
    "performance",
    "awd",
    "dual motor",
    "trazione integrale",
]
