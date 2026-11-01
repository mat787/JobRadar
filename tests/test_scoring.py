import pytest

from rag.scoring import compute_score, required_months


def checks(*statuses):
    return [{"status": s} for s in statuses]


def test_all_met_without_experience_requirement_gives_100():
    assert compute_score(checks("met", "met"), checks("met"), months=3, needed_months=None) == 100


def test_nothing_met_gives_0():
    assert compute_score(checks("missing", "missing"), checks("missing"), months=0, needed_months=12) == 0


def test_partial_counts_as_half():
    assert compute_score(checks("partial", "partial"), [], months=0, needed_months=None) == 50


def test_missing_sections_do_not_lower_the_score():
    assert compute_score(checks("met"), [], months=0, needed_months=None) == 100


def test_experience_is_capped_at_requirement():
    full = compute_score(checks("met"), [], months=24, needed_months=12)
    exact = compute_score(checks("met"), [], months=12, needed_months=12)
    assert full == exact == 100


def test_wierzbicki_offer_is_in_a_realistic_range():
    requirements = checks("missing", "met", "missing", "met", "missing", "met", "missing", "met", "met")
    nice = checks("met", "met", "missing", "missing", "missing", "missing", "missing")
    assert 40 <= compute_score(requirements, nice, months=3.8, needed_months=12) <= 60


@pytest.mark.parametrize("text, months", [
    (["Min. 1 rok doświadczenia komercyjnego na podobnym stanowisku"], 12),
    (["Minimum 2–3 lata doświadczenia w testowaniu oprogramowania."], 24),
    (["3+ years of experience with Python"], 36),
    (["Minimum 5 lat doświadczenia w pracy jako Programista Python"], 60),
    (["Bardzo dobra znajomość SQL"], None),
    (["Rok założenia firmy 2010"], None),
])
def test_required_months(text, months):
    assert required_months(text) == months
