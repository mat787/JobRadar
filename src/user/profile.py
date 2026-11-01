import hashlib
import os
import re
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

PROFILE = {
    "name": "Matylda D.",
    "headline": "Studentka III roku Informatyki Stosowanej (PW), Junior Data Analyst",
    "skills": [
        "Python", "SQL", "R", "Java", "C", "MATLAB",
        "Pandas", "Scikit-learn", "dplyr", "ggplot2", "Streamlit",
        "PostgreSQL", "SQLite", "Snowflake", "Apache Drill",
        "Google Cloud Platform", "Azure", "Docker", "Git", "Linux", "FastAPI",
        "Jupyter Notebook", "QGIS", "Excel", "Jira", "Agile", "Scrum",
    ],
    "experience": [
        {"title": "Data Engineering and Analytics Intern", "company": "REDS S.A.",
         "kind": "internship", "start": date(2026, 7, 1), "end": date(2026, 9, 30)},
        {"title": "Junior Data Analyst", "company": "REDS S.A.",
         "kind": "job", "start": date(2026, 10, 1), "end": None},
        {"title": "Core Team Member", "company": "GDG on Campus PW",
         "kind": "organization", "start": date(2026, 2, 1), "end": None},
        {"title": "Tech Ambassador", "company": "EY",
         "kind": "organization", "start": date(2026, 10, 1), "end": None},
    ],
}

ALIASES = {
    "microsoft azure": "azure",
    "gcp": "google cloud platform",
    "postgres": "postgresql",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
}


def normalize(skill):
    key = " ".join(skill.lower().split())
    return ALIASES.get(key, key)


SKILL_KEYS = {normalize(s) for s in PROFILE["skills"]}


def has_skill(name):
    return normalize(name) in SKILL_KEYS


def commercial_months(today=None):
    """Staż komercyjny w miesiącach: praca i staże, nakładające się okresy liczone raz."""
    today = today or date.today()
    periods = sorted(
        (e["start"], e["end"] or today)
        for e in PROFILE["experience"]
        if e["kind"] in ("job", "internship")
    )
    merged = []
    for start, end in periods:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    days = sum((end - start).days + 1 for start, end in merged)
    return round(days / 30.44, 1)


CONTACT_PATTERN = re.compile(r'(\+?\d[\d\s-]{7,}\d)|([\w.+-]+@[\w-]+\.[\w.]+)')
CONSENT_PATTERN = re.compile(r'wyrażam zgodę na przetwarzanie', re.IGNORECASE)


def load_cv_text():
    """Tekst CV z pliku wskazanego w CV_PATH (bez telefonu, maila i klauzuli RODO).

    Plik leży poza repozytorium, więc treść CV nie trafia do gita.
    Gdy CV_PATH nie jest ustawione, składa skrócone CV z danych profilu.
    """
    load_dotenv()
    path = os.environ.get("CV_PATH")
    if path and Path(path).exists():
        if path.lower().endswith(".pdf"):
            from userExtraction.pdfConverter import PdfTextExtractor
            raw = PdfTextExtractor(path).get_text()
        else:
            from userExtraction.docxConverter import DocxTextExtractor
            raw = DocxTextExtractor(path).get_text()
        lines = []
        for line in raw.splitlines():
            if CONSENT_PATTERN.search(line):
                continue
            line = CONTACT_PATTERN.sub("", line)
            line = re.sub(r'(\s*\|\s*)+', ' | ', line).strip(' |')
            if line:
                lines.append(line)
        return "\n".join(lines)

    experience = "\n".join(
        f"- {e['title']}, {e['company']} ({e['start']:%m/%Y} – {e['end'].strftime('%m/%Y') if e['end'] else 'obecnie'})"
        for e in PROFILE["experience"]
    )
    return f"{PROFILE['name']}\n{PROFILE['headline']}\n\nDOŚWIADCZENIE\n{experience}\n\nUMIEJĘTNOŚCI\n{', '.join(PROFILE['skills'])}"


def cv_hash(cv_text):
    return hashlib.sha1(cv_text.encode("utf-8")).hexdigest()[:16]
