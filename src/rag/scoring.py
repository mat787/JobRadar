import re

STATUS_VALUE = {"met": 1.0, "partial": 0.5, "missing": 0.0}

WEIGHT_REQUIREMENTS = 70
WEIGHT_NICE_TO_HAVE = 15
WEIGHT_EXPERIENCE = 15

YEARS_PATTERN = re.compile(
    r'(?:min(?:imum|\.)?\s*)?(\d+(?:[.,]\d+)?)\s*(?:\+|\s*[-–—]\s*\d+)?\s*(?:rok|lat|lata|year|years|yrs)\b',
    re.IGNORECASE,
)
EXPERIENCE_HINT = re.compile(r'do[śs]wiadcz|experience', re.IGNORECASE)


def required_months(requirements):
    """Najmniejszy wymagany staż w miesiącach wyczytany z wymagań (None, gdy oferta go nie podaje)."""
    found = []
    for text in requirements:
        if not EXPERIENCE_HINT.search(text):
            continue
        for match in YEARS_PATTERN.finditer(text):
            found.append(float(match.group(1).replace(',', '.')) * 12)
    return min(found) if found else None


def share(checks):
    if not checks:
        return None
    return sum(STATUS_VALUE[c["status"]] for c in checks) / len(checks)


def compute_score(requirements, nice_to_have, months, needed_months):
    """Wynik dopasowania 0–100 liczony w kodzie (nie przez LLM).

    requirements / nice_to_have: listy ocen {"status": "met"|"partial"|"missing"}
    months: staż komercyjny kandydatki, needed_months: wymagany staż (None = brak wymogu)
    Brakujące sekcje nie obniżają wyniku — ich waga przechodzi proporcjonalnie na pozostałe.
    """
    parts = []
    if (req := share(requirements)) is not None:
        parts.append((WEIGHT_REQUIREMENTS, req))
    if (nice := share(nice_to_have)) is not None:
        parts.append((WEIGHT_NICE_TO_HAVE, nice))
    if needed_months:
        parts.append((WEIGHT_EXPERIENCE, min(months / needed_months, 1.0)))
    if not parts:
        return 0
    total_weight = sum(w for w, _ in parts)
    return round(100 * sum(w * v for w, v in parts) / total_weight)
