import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from rag.documents import build_offer_prompt
from rag.scoring import compute_score, required_months

PROMPT_VERSION = 2

SYSTEM_PROMPT = """Jesteś doradcą kariery w IT. Oceniasz, czy CV kandydatki spełnia wymagania oferty pracy.

Zasady:
- Opieraj się WYŁĄCZNIE na CV i ofercie. Jeśli czegoś nie ma w CV, status to "missing".
- "met": CV wprost potwierdza wymaganie. "partial": CV potwierdza część wymagania albo pośrednio. "missing": brak potwierdzenia.
- evidence: krótki, DOSŁOWNY cytat z CV (do 120 znaków) dla "met" i "partial"; dla "missing" pusty tekst.
- Wymagania dotyczące stażu oceniaj na podstawie podanego stażu komercyjnego w miesiącach — nie licz go z dat.
- Oceń KAŻDE wymaganie i KAŻDY punkt "mile widziane": dokładnie jeden wpis na numer.
- cv_tips: 2–4 konkretne wskazówki (co dopisać, przeformułować, wyeksponować). Nie sugeruj umiejętności, których kandydatka nie ma.
- summary: 2 zdania po polsku, szczerze: co przemawia za kandydaturą i czego brakuje.
- Pisz wyłącznie po polsku."""


class RequirementCheck(BaseModel):
    id: int = Field(description="numer wymagania z oferty")
    status: Literal["met", "partial", "missing"]
    evidence: str = Field(description="dosłowny cytat z CV albo pusty tekst")


class MatchAnalysis(BaseModel):
    requirements: list[RequirementCheck]
    nice_to_have: list[RequirementCheck]
    cv_tips: list[str]
    summary: str


FOREIGN_SCRIPT = re.compile(r'[Ѐ-ӿͰ-Ͽ֐-׿؀-ۿ一-鿿]')


def normalize(text):
    text = text.lower().replace('„', '"').replace('”', '"').replace('’', "'")
    return ' '.join(re.sub(r'["\'«»]', ' ', text).split())


def evidence_in_cv(evidence, cv_norm):
    """Czy cytat naprawdę występuje w CV. Model łączy czasem kilka cytatów wielokropkiem,
    średnikiem albo „|” — wtedy każdy fragment musi występować w CV osobno."""
    fragments = [f.strip(' .,') for f in re.split(r'…|\.\.\.|;|\|', normalize(evidence))]
    fragments = [f for f in fragments if len(f) >= 6]
    return bool(fragments) and all(f in cv_norm for f in fragments)


def build_user_prompt(cv_text, months, offer_row, today=None):
    """Stałe elementy (data, staż, CV) na początku — LM Studio używa wtedy pamięci podręcznej prefiksu."""
    today = today or date.today()
    return (
        f"Dzisiejsza data: {today:%d.%m.%Y}\n"
        f"Staż komercyjny kandydatki: {str(months).replace('.', ',')} mies.\n\n"
        f"CV:\n{cv_text}\n\n"
        f"{build_offer_prompt(offer_row)}"
    )


class MatchAnalyzer:
    """Ocenia dopasowanie CV do oferty: Gemma ocenia wymagania, kod sprawdza odpowiedź i liczy wynik."""

    def __init__(self, chat, max_attempts=2):
        self.chat = chat
        self.max_attempts = max_attempts

    def analyze(self, cv_text, months, offer_row):
        user_prompt = build_user_prompt(cv_text, months, offer_row)
        cv_norm = normalize(cv_text)
        n_req, n_nice = len(offer_row['requirements']), len(offer_row['nice_to_have'])

        for attempt in range(1, self.max_attempts + 1):
            response = self.chat.structured(SYSTEM_PROMPT, user_prompt, MatchAnalysis)
            analysis, flags = self.check(response.data, n_req, n_nice, cv_norm)
            retry_flags = {'foreign_script', 'missing_requirements'}
            if not retry_flags & set(flags) or attempt == self.max_attempts:
                break

        needed = required_months(offer_row['requirements'])
        requirements = [c.model_dump() for c in analysis.requirements]
        nice = [c.model_dump() for c in analysis.nice_to_have]
        return {
            "model": self.chat.model,
            "score": compute_score(requirements, nice, months, needed),
            "flags": flags,
            "duration_ms": response.duration_ms,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "result": {
                "requirements": requirements,
                "nice_to_have": nice,
                "cv_tips": analysis.cv_tips,
                "summary": analysis.summary,
                "months": months,
                "required_months": needed,
                "attempts": attempt,
            },
        }

    @staticmethod
    def check(analysis, n_req, n_nice, cv_norm):
        """Kontrola jakości: numery, kompletność, cytaty naprawdę z CV, obce alfabety."""
        flags = []
        for field, count in (("requirements", n_req), ("nice_to_have", n_nice)):
            checks = {}
            for c in getattr(analysis, field):
                if 1 <= c.id <= count and c.id not in checks:
                    checks[c.id] = c
            if len(checks) < count:
                flags.append('missing_requirements')
                for i in range(1, count + 1):
                    checks.setdefault(i, RequirementCheck(id=i, status="missing", evidence=""))
            for c in checks.values():
                if c.status == "missing":
                    c.evidence = ""
                elif not evidence_in_cv(c.evidence, cv_norm):
                    c.status = "partial" if c.evidence else "missing"
                    flags.append('evidence_not_in_cv')
            setattr(analysis, field, [checks[i] for i in sorted(checks)])

        texts = [analysis.summary, *analysis.cv_tips]
        if any(FOREIGN_SCRIPT.search(t) for t in texts):
            flags.append('foreign_script')
        return analysis, sorted(set(flags))
