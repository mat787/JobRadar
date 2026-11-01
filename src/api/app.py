from pathlib import Path

from functools import lru_cache

import openai
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from psycopg.rows import dict_row

from database.connection import Database
from llm.chat import ChatClient
from llm.embedder import Embedder
from rag.service import RagService
from user.profile import PROFILE, commercial_months, has_skill

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
LEVEL_PATTERNS = {"junior": "%junior%", "mid": "%mid%", "senior": "%senior%"}
ACTIVE = "o.is_active"

app = FastAPI(title="JobRadar API")


def fetch_all(sql, params=()):
    with Database() as db:
        with db.conn.cursor(row_factory=dict_row) as cur:
            return cur.execute(sql, params).fetchall()


def level_clause(level, params):
    if level not in LEVEL_PATTERNS:
        return None
    params.append(LEVEL_PATTERNS[level])
    return "EXISTS (SELECT 1 FROM unnest(o.levels) l WHERE l ILIKE %s)"


def tech_list(names):
    return [{"name": n, "have": has_skill(n)} for n in names]


def coverage(names):
    have = sum(1 for n in names if has_skill(n))
    return {"have": have, "total": len(names)}


@app.get("/api/summary")
def summary():
    row = fetch_all(f"""
        SELECT count(*) AS total,
               count(*) FILTER (WHERE EXISTS (SELECT 1 FROM unnest(o.levels) l WHERE l ILIKE '%%junior%%')) AS junior,
               count(*) FILTER (WHERE cardinality(o.technologies) > 0) AS with_technologies,
               count(*) FILTER (WHERE {ACTIVE}) AS active,
               count(o.details_fetched_at) AS with_details,
               max(o.last_seen) AS updated_at
        FROM offers o
    """)[0]
    return row


@app.get("/api/stats/technologies")
def technologies(level: str = "all", limit: int = Query(12, le=50)):
    params = []
    where = level_clause(level, params)
    rows = fetch_all(f"""
        SELECT t AS name, count(*) AS count
        FROM offers o, unnest(o.technologies) t
        {"WHERE " + where if where else ""}
        GROUP BY t ORDER BY count DESC, t LIMIT %s
    """, (*params, limit))
    return [{**r, "have": has_skill(r["name"])} for r in rows]


@app.get("/api/stats/levels")
def levels():
    return fetch_all("""
        SELECT l AS name, count(*) AS count
        FROM offers o, unnest(o.levels) l
        GROUP BY l ORDER BY count DESC
    """)


@app.get("/api/offers")
def offers(
    q: str = "",
    level: str = "all",
    tech: list[str] = Query(default=[]),
    work_mode: str = "",
    sort: str = "newest",
    active: bool = True,
    limit: int = Query(30, le=100),
    offset: int = 0,
):
    params, clauses = [], []
    if active:
        clauses.append(ACTIVE)
    if q.strip():
        clauses.append("(o.title ILIKE %s OR o.company ILIKE %s OR o.description ILIKE %s)")
        params += [f"%{q.strip()}%"] * 3
    if (lc := level_clause(level, params)):
        clauses.append(lc)
    if tech:
        clauses.append("o.technologies @> %s")
        params.append(tech)
    if work_mode:
        clauses.append("%s = ANY(o.work_modes)")
        params.append(work_mode)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    order = {
        "newest": "o.published_at DESC NULLS LAST, o.first_seen DESC",
        "expiring": "o.expires_at ASC NULLS LAST",
    }.get(sort, "o.published_at DESC NULLS LAST")

    rows = fetch_all(f"""
        SELECT o.id, o.title, o.company, o.salary, o.locations, o.work_modes, o.levels,
               o.technologies, o.expires_at, o.published_at, count(*) OVER () AS total_count
        FROM offers o {where}
        ORDER BY {order}
        LIMIT %s OFFSET %s
    """, (*params, limit, offset))
    total = rows[0]["total_count"] if rows else 0
    items = [{
        **{k: v for k, v in r.items() if k not in ("total_count", "technologies")},
        "technologies": tech_list(r["technologies"]),
        "coverage": coverage(r["technologies"]),
    } for r in rows]
    return {"total": total, "items": items}


@app.get("/api/offers/{offer_id}")
def offer(offer_id: str):
    rows = fetch_all("SELECT * FROM offers WHERE id = %s", (offer_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Nie ma takiej oferty")
    r = rows[0]
    return {
        **{k: v for k, v in r.items() if k not in ("technologies", "technologies_optional")},
        "technologies": tech_list(r["technologies"]),
        "technologies_optional": tech_list(r["technologies_optional"]),
        "coverage": coverage(r["technologies"]),
        "coverage_optional": coverage(r["technologies_optional"]),
    }


@app.get("/api/profile")
def profile():
    return {**PROFILE, "commercial_months": commercial_months()}


@lru_cache
def models():
    return Embedder(), ChatClient()


def with_rag(action):
    """Uruchamia akcję na RagService; błąd połączenia z LM Studio zamienia na czytelne 503."""
    embedder, chat = models()
    try:
        with Database() as db:
            return action(RagService(db, embedder, chat))
    except openai.APIConnectionError:
        raise HTTPException(status_code=503, detail="Brak połączenia z LM Studio — uruchom serwer z modelami.")


@app.get("/api/match")
def match(level: str = "all", limit: int = Query(30, le=100)):
    return with_rag(lambda rag: rag.match_profile(level=level, limit=limit))


@app.get("/api/search")
def semantic_search(q: str, level: str = "all", limit: int = Query(30, le=100)):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Podaj tekst do wyszukania")
    return with_rag(lambda rag: rag.search(q, level=level, limit=limit))


@app.get("/api/offers/{offer_id}/analysis")
def get_analysis(offer_id: str):
    return with_rag(lambda rag: rag.cached_analysis(offer_id))


@app.post("/api/offers/{offer_id}/analysis")
def run_analysis(offer_id: str, force: bool = False):
    result = with_rag(lambda rag: rag.analyze_offer(offer_id, force=force))
    if result is None:
        raise HTTPException(status_code=404, detail="Nie ma takiej oferty")
    return result


class FrontendFiles(StaticFiles):
    """Pliki frontendu; przeglądarka musi sprawdzić, czy się zmieniły, zamiast używać starej kopii."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


app.mount("/", FrontendFiles(directory=FRONTEND_DIR, html=True), name="frontend")
