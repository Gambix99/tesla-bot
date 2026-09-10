from config import EXCLUDE_TRIM_KEYWORDS


def is_rwd_base_model3(vehicle: dict) -> bool:
    """True se il veicolo è la Model 3 base a trazione posteriore
    (cioè non Long Range, non Performance, non AWD)."""
    trim_name = (vehicle.get("TrimName") or "").lower()
    return not any(keyword in trim_name for keyword in EXCLUDE_TRIM_KEYWORDS)
