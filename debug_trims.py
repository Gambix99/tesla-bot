"""
Script diagnostico: stampa le versioni (TrimName) e i campi grezzi che
Tesla restituisce davvero per le Model 3 in Italia, così puoi verificare
che il filtro in filters.py stia isolando correttamente la trazione
posteriore. Utile anche per scoprire nuovi campi (es. nomi colore).

Uso: python debug_trims.py
"""
import json

from filters import is_rwd_base_model3
from tesla_api import get_model3_all_trims


def main() -> None:
    vehicles = get_model3_all_trims()
    print(f"Totale Model 3 trovate in Italia: {len(vehicles)}\n")

    trims_seen = {}
    for v in vehicles:
        trim = v.get("TrimName", "N/D")
        trims_seen.setdefault(trim, {"count": 0, "rwd_match": None})
        trims_seen[trim]["count"] += 1
        trims_seen[trim]["rwd_match"] = is_rwd_base_model3(v)

    print("Versioni (TrimName) trovate e se vengono classificate come RWD dal filtro:")
    for trim, info in trims_seen.items():
        marker = "✅ RWD" if info["rwd_match"] else "❌ esclusa"
        print(f"  - '{trim}': {info['count']} auto -> {marker}")

    if vehicles:
        print("\nEsempio di record grezzo restituito da Tesla (primo veicolo):")
        print(json.dumps(vehicles[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
