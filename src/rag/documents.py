TEXT_VERSION = 1


def add_list(parts, label, items):
    if items:
        parts.append(f"{label}:\n" + "\n".join(f"- {item}" for item in items))


def build_offer_text(row):
    """Tekst oferty do embeddingu: tylko to, co opisuje pracę (bez benefitów i marketingu)."""
    parts = [f"Stanowisko: {row['title']}"]
    if row['technologies']:
        parts.append("Technologie: " + ", ".join(row['technologies']))
    if row['technologies_optional']:
        parts.append("Technologie opcjonalne: " + ", ".join(row['technologies_optional']))
    add_list(parts, "Wymagania", row['requirements'])
    add_list(parts, "Mile widziane", row['nice_to_have'])
    add_list(parts, "Zakres obowiązków", row['responsibilities'])
    if row['about_project']:
        parts.append("O projekcie: " + row['about_project'][:1000])
    return "\n".join(parts)


def numbered(items):
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, start=1))


def build_offer_prompt(row):
    """Oferta do analizy przez LLM: ponumerowane wymagania, żeby model odpowiadał numerami."""
    parts = [f"OFERTA: {row['title']}" + (f" — {row['company']}" if row.get('company') else "")]
    if row['technologies']:
        parts.append("Technologie: " + ", ".join(row['technologies']))
    parts.append("WYMAGANIA:\n" + (numbered(row['requirements']) if row['requirements'] else "(brak)"))
    parts.append("MILE WIDZIANE:\n" + (numbered(row['nice_to_have']) if row['nice_to_have'] else "(brak)"))
    if row['about_project']:
        parts.append("O PROJEKCIE: " + row['about_project'][:600])
    return "\n\n".join(parts)
