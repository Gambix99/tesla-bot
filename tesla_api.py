"""
Client minimale per l'API "inventory-results" di Tesla.

NOTA IMPORTANTE:
Questa non è un'API ufficiale/documentata da Tesla: è lo stesso endpoint
JSON che il sito tesla.com interroga internamente quando visiti la pagina
"Pronta consegna". Funziona bene ma può cambiare senza preavviso.

Se in futuro il bot smette di trovare risultati:
1. Vai su https://www.tesla.com/it_it/inventory/new/m3 con Chrome/Firefox
2. Apri gli strumenti sviluppatore (F12) -> tab "Rete/Network"
3. Filtra per "inventory-results"
4. Ricarica la pagina e clicca sulla richiesta che compare
5. Copia il valore del parametro "query" (decodificato) e confrontalo
   con quello generato da _build_query() qui sotto: aggiorna i campi
   che risultano diversi (es. nomi dei TRIM, market, super_region...).
"""
from __future__ import annotations

import json
import logging
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.tesla.com/inventory/api/v4/inventory-results"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.tesla.com/it_it/inventory/new/m3",
}

# Punto geografico "neutro" (Roma), usato solo come centro di ricerca.
# Con outsideSearch=True l'API restituisce comunque risultati su tutta
# Italia, coerentemente con la richiesta di non porre limiti di distanza.
DEFAULT_LAT = 41.9028
DEFAULT_LNG = 12.4964
DEFAULT_ZIP = "00100"

REQUEST_TIMEOUT = 20


def _build_query(model: str, options: dict | None, outside_search: bool) -> dict:
    return {
        "query": {
            "model": model,
            "condition": "new",
            "options": options or {},
            "arrangeby": "Price",
            "order": "asc",
            "market": "IT",
            "language": "it",
            "lng": DEFAULT_LNG,
            "lat": DEFAULT_LAT,
            "zip": DEFAULT_ZIP,
            "range": 0,
        },
        "offset": 0,
        "count": 100,
        "outsideOffset": 0,
        "outsideSearch": outside_search,
    }


def _fetch(model: str, options: dict | None = None) -> list[dict]:
    """Interroga l'endpoint sia in modalità 'locale' sia 'outsideSearch'
    (necessaria per coprire tutto il territorio nazionale) e unisce i
    risultati deduplicandoli per VIN."""
    results: dict[str, dict] = {}
    for outside in (False, True):
        query = _build_query(model, options, outside_search=outside)
        url = f"{BASE_URL}?query={quote(json.dumps(query))}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # rete, timeout, blocco anti-bot, JSON malformato...
            logger.warning("Errore chiamata Tesla API model=%s outside=%s: %s", model, outside, exc)
            continue

        for vehicle in data.get("results", []):
            vin = vehicle.get("VIN")
            if vin:
                results[vin] = vehicle

    return list(results.values())


def get_model3_all_trims() -> list[dict]:
    """Tutte le Model 3 nuove in pronta consegna in Italia (ogni versione)."""
    return _fetch("m3")


def get_full_inventory() -> list[dict]:
    """Tutte le auto Tesla nuove in pronta consegna in Italia, tutti i modelli."""
    all_vehicles: list[dict] = []
    for model in ("ms", "m3", "mx", "my"):
        all_vehicles.extend(_fetch(model))
    return all_vehicles
