from datetime import date

from rag.analyzer import MatchAnalysis, MatchAnalyzer, RequirementCheck, build_user_prompt, normalize
from user.profile import commercial_months

CV = normalize("Analiza danych operacyjnych kolei w SQL (Apache Drill) – CTE, window functions\nPython, SQL, R, Java")


def analysis(requirements, nice=(), tips=("Dopisz testy",), summary="Dobre podstawy."):
    return MatchAnalysis(requirements=list(requirements), nice_to_have=list(nice), cv_tips=list(tips), summary=summary)


def test_quote_from_cv_keeps_met_status():
    a, flags = MatchAnalyzer.check(analysis([RequirementCheck(id=1, status="met", evidence="„window functions”")]), 1, 0, CV)
    assert a.requirements[0].status == "met" and flags == []


def test_quotes_joined_with_semicolon_are_checked_separately():
    evidence = "window functions; Python, SQL, R"
    a, flags = MatchAnalyzer.check(analysis([RequirementCheck(id=1, status="met", evidence=evidence)]), 1, 0, CV)
    assert a.requirements[0].status == "met" and flags == []


def test_joined_quote_with_one_invented_part_is_flagged():
    evidence = "window functions; 3 lata w Kubernetes"
    _, flags = MatchAnalyzer.check(analysis([RequirementCheck(id=1, status="met", evidence=evidence)]), 1, 0, CV)
    assert "evidence_not_in_cv" in flags


def test_invented_quote_is_downgraded_and_flagged():
    a, flags = MatchAnalyzer.check(analysis([RequirementCheck(id=1, status="met", evidence="5 lat w Kubernetes")]), 1, 0, CV)
    assert a.requirements[0].status == "partial"
    assert "evidence_not_in_cv" in flags


def test_missing_requirement_numbers_are_filled_and_flagged():
    a, flags = MatchAnalyzer.check(analysis([RequirementCheck(id=2, status="met", evidence="Python, SQL")]), 3, 0, CV)
    assert [c.id for c in a.requirements] == [1, 2, 3]
    assert [c.status for c in a.requirements] == ["missing", "met", "missing"]
    assert "missing_requirements" in flags


def test_foreign_script_is_flagged():
    _, flags = MatchAnalyzer.check(analysis([], summary="Dobre знания SQL."), 0, 0, CV)
    assert "foreign_script" in flags


def test_prompt_starts_with_stable_prefix():
    offer = {"title": "A", "company": "B", "technologies": [], "requirements": ["x"], "nice_to_have": [], "about_project": None}
    other = {**offer, "title": "Inna oferta", "requirements": ["y", "z"]}
    first = build_user_prompt("CV", 3.8, offer, today=date(2026, 10, 24))
    second = build_user_prompt("CV", 3.8, other, today=date(2026, 10, 24))
    prefix = "Dzisiejsza data: 24.10.2026\nStaż komercyjny kandydatki: 3,8 mies.\n\nCV:\nCV\n\n"
    assert first.startswith(prefix) and second.startswith(prefix)


def test_commercial_months_merges_internship_and_job():
    assert commercial_months(today=date(2026, 10, 24)) == 3.8
