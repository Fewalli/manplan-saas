def dhm_to_minutes(days: int, hours: int, minutes: int) -> int:
    if not (0 <= days <= 30):
        raise ValueError("Dias deve estar entre 0 e 30.")
    if not (0 <= hours <= 23):
        raise ValueError("Horas deve estar entre 0 e 23.")
    if not (0 <= minutes <= 59):
        raise ValueError("Minutos deve estar entre 0 e 59.")
    return days * 1440 + hours * 60 + minutes