"""
Versione "cloud" del bot: pensata per essere avviata periodicamente da
GitHub Actions invece che restare sempre accesa su un computer.

Ad ogni esecuzione:
  1. Legge lo stato salvato in state.json (VIN già notificati, ultimo
     messaggio Telegram letto, quando è stato fatto l'ultimo controllo
     dell'inventory).
  2. Controlla se ci sono comandi Telegram in sospeso (/start, /lista,
     /model3, /check) e risponde.
  3. Se sono passati almeno CHECK_INTERVAL_SECONDS dall'ultimo controllo
     dell'inventory (oppure se è stato chiesto /check), interroga Tesla
     e notifica le nuove Model 3 a trazione posteriore.
  4. Salva lo stato aggiornato in state.json (il workflow GitHub Actions
     fa il commit del file se è cambiato, così lo stato sopravvive tra
     un'esecuzione e l'altra).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

from filters import is_rwd_base_model3
from notifier import format_vehicle_line, send_email
from tesla_api import get_full_inventory, get_model3_all_trims

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  # usato per le notifiche automatiche
CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_SECONDS", "1800"))

STATE_FILE = Path(__file__).parent / "state.json"
API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
MAX_MSG_LEN = 3500


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"seen_vins": [], "last_update_id": 0, "last_inventory_check": 0}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _post_message(chat_id, text: str) -> None:
    try:
        requests.post(
            f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=15
        )
    except Exception as exc:
        print(f"Errore invio messaggio Telegram: {exc}")


def send_message(chat_id, text: str) -> None:
    """Spezza il messaggio se supera il limite di lunghezza di Telegram."""
    chunk = ""
    for line in text.split("\n"):
        if len(chunk) + len(line) + 1 > MAX_MSG_LEN:
            _post_message(chat_id, chunk)
            chunk = ""
        chunk += line + "\n"
    if chunk.strip():
        _post_message(chat_id, chunk)


def format_list(vehicles: list[dict], empty_message: str) -> str:
    if not vehicles:
        return empty_message
    lines = [format_vehicle_line(v) for v in vehicles]
    return f"Trovate {len(vehicles)} auto:\n\n" + "\n".join(lines)


def handle_commands(state: dict) -> bool:
    """Legge ed evade i comandi Telegram in sospeso.
    Ritorna True se è stato richiesto un controllo forzato (/check)."""
    offset = state.get("last_update_id", 0) + 1
    try:
        resp = requests.get(
            f"{API_URL}/getUpdates", params={"offset": offset, "timeout": 0}, timeout=15
        )
        resp.raise_for_status()
        updates = resp.json().get("result", [])
    except Exception as exc:
        print(f"Errore lettura comandi Telegram: {exc}")
        return False

    force_check = False
    for update in updates:
        state["last_update_id"] = update["update_id"]
        message = update.get("message") or update.get("edited_message")
        if not message or "text" not in message:
            continue

        chat_id = message["chat"]["id"]
        # Se è configurato TELEGRAM_CHAT_ID, rispondi solo a quella chat (sicurezza)
        if TELEGRAM_CHAT_ID and str(chat_id) != str(TELEGRAM_CHAT_ID):
            continue

        text = message["text"].strip().split("@")[0]  # rimuove un eventuale @nomebot

        if text == "/start":
            send_message(
                chat_id,
                "Ciao! Ti avviso quando compare una nuova Model 3 a trazione "
                "posteriore in pronta consegna su Tesla Italia.\n\n"
                "Comandi disponibili:\n"
                "/lista — tutte le auto Tesla in pronta consegna in Italia\n"
                "/model3 — solo le Model 3 a trazione posteriore\n"
                "/check — forza subito un controllo\n\n"
                "Nota: le risposte possono richiedere qualche minuto, "
                "perché il bot si attiva periodicamente e non resta sempre acceso.",
            )
        elif text == "/lista":
            send_message(chat_id, "Sto controllando il sito Tesla, un attimo...")
            vehicles = get_full_inventory()
            send_message(
                chat_id,
                format_list(vehicles, "Nessuna auto Tesla in pronta consegna al momento."),
            )
        elif text == "/model3":
            send_message(chat_id, "Sto controllando le Model 3, un attimo...")
            vehicles = [v for v in get_model3_all_trims() if is_rwd_base_model3(v)]
            send_message(
                chat_id,
                format_list(
                    vehicles, "Nessuna Model 3 a trazione posteriore in pronta consegna al momento."
                ),
            )
        elif text == "/check":
            send_message(chat_id, "Controllo forzato in corso...")
            force_check = True

    return force_check


def check_inventory(state: dict) -> None:
    vehicles = get_model3_all_trims()
    rwd_vehicles = [v for v in vehicles if is_rwd_base_model3(v)]
    current_vins = {v["VIN"] for v in rwd_vehicles if v.get("VIN")}

    seen = set(state.get("seen_vins", []))
    new_vins = current_vins - seen

    if new_vins:
        new_vehicles = [v for v in rwd_vehicles if v.get("VIN") in new_vins]
        lines = [format_vehicle_line(v) for v in new_vehicles]
        text = (
            f"🚗 Trovate {len(new_vehicles)} nuova/e Model 3 a trazione posteriore "
            f"in pronta consegna:\n\n" + "\n".join(lines)
        )
        if TELEGRAM_CHAT_ID:
            send_message(TELEGRAM_CHAT_ID, text)
        send_email("Nuova Model 3 a trazione posteriore disponibile", text)
        print(f"Notifica inviata per {len(new_vehicles)} nuovi veicoli")
    else:
        print(f"Nessuna novità (totale attuale: {len(current_vins)})")

    state["seen_vins"] = sorted(current_vins)
    state["last_inventory_check"] = time.time()


def main() -> None:
    state = load_state()

    force_check = handle_commands(state)

    elapsed = time.time() - state.get("last_inventory_check", 0)
    if force_check or elapsed >= CHECK_INTERVAL_SECONDS:
        try:
            check_inventory(state)
        except Exception as exc:
            print(f"Controllo inventory fallito: {exc}")

    save_state(state)


if __name__ == "__main__":
    main()
