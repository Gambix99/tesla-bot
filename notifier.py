import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

logger = logging.getLogger(__name__)

# Mappa non esaustiva dei codici colore Tesla più comuni.
# Se un'auto ha un codice non presente qui, viene mostrato il codice grezzo.
PAINT_CODES = {
    "PBSB": "Nero Solido",
    "PPSW": "Bianco Perla Multicoat",
    "PBCW": "Bianco",
    "PPMR": "Rosso Multicoat",
    "PPSB": "Blu Profondo Metallizzato",
    "PMNG": "Grigio Argento Metallizzato",
    "PN02": "Argento Lunare",
    "PMBL": "Nero Ossidiana Metallizzato",
    "PB800": "Blu Ghiaccio Metallizzato",
}

MODEL_NAMES = {"ms": "Model S", "m3": "Model 3", "mx": "Model X", "my": "Model Y"}


def _price_str(vehicle: dict) -> str:
    price = vehicle.get("Price") or vehicle.get("TotalPrice") or vehicle.get("PurchasePrice")
    if isinstance(price, (int, float)):
        return f"{price:,.0f} €".replace(",", ".")
    return "prezzo N/D"


def _color_str(vehicle: dict) -> str:
    paint = vehicle.get("PAINT")
    code = paint[0] if isinstance(paint, list) and paint else None
    if not code:
        return "colore N/D"
    return PAINT_CODES.get(code, code)


def _model_str(vehicle: dict) -> str:
    model_code = (vehicle.get("Model") or "").lower()
    return MODEL_NAMES.get(model_code, vehicle.get("Model", "Tesla"))


def format_vehicle_line(vehicle: dict) -> str:
    trim = vehicle.get("TrimName", "N/D")
    location = vehicle.get("MetroName") or vehicle.get("City") or "N/D"
    vin = vehicle.get("VIN", "")
    vin_suffix = vin[-6:] if vin else "N/D"
    return (
        f"• {_model_str(vehicle)} — {trim} — {_color_str(vehicle)} — "
        f"{_price_str(vehicle)} — {location} (VIN ...{vin_suffix})"
    )


def send_email(subject: str, body: str) -> None:
    if not config.EMAIL_ENABLED:
        return
    if not (config.SMTP_USER and config.SMTP_PASSWORD and config.EMAIL_TO):
        logger.warning("Email abilitata ma configurazione incompleta (SMTP_USER/SMTP_PASSWORD/EMAIL_TO): invio saltato.")
        return

    msg = MIMEMultipart()
    msg["From"] = config.EMAIL_FROM
    msg["To"] = config.EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Email di notifica inviata a %s", config.EMAIL_TO)
    except Exception as exc:
        logger.error("Errore invio email: %s", exc)
