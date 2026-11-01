import numpy as np
from psycopg.rows import dict_row

from user.profile import has_skill

LEVEL_PATTERNS = {"junior": "%junior%", "mid": "%mid%", "senior": "%senior%"}
SEMANTIC_WEIGHT = 0.7
TECH_WEIGHT = 0.3
NEUTRAL_COVERAGE = 0.5


class OfferRetriever:
    """Wyszukuje oferty podobne do tekstu (CV albo zapytania): wektory + pokrycie technologii + filtry SQL."""

    def __init__(self, db, embedder):
        self.db = db
        self.embedder = embedder

    def search(self, query_text, *, level=None, active=True, limit=20, pool=150):
        vector = np.array(self.embedder.embed_one(query_text), dtype=np.float32)
        clauses, params = [], [vector]
        if active:
            clauses.append("o.is_active")
        if level in LEVEL_PATTERNS:
            clauses.append("EXISTS (SELECT 1 FROM unnest(o.levels) l WHERE l ILIKE %s)")
            params.append(LEVEL_PATTERNS[level])
        where = "WHERE " + " AND ".join(clauses) if clauses else ""

        with self.db.conn.cursor(row_factory=dict_row) as cur:
            rows = cur.execute(
                f"""
                SELECT o.id, o.title, o.company, o.salary, o.locations, o.work_modes, o.levels,
                       o.technologies, o.expires_at, 1 - (e.embedding <=> %s) AS semantic
                FROM offer_embeddings e
                JOIN offers o ON o.id = e.offer_id
                {where}
                ORDER BY e.embedding <=> %s
                LIMIT %s
                """,
                (*params, vector, pool),
            ).fetchall()
        return self.rank(rows)[:limit]

    @staticmethod
    def rank(rows):
        """Ranking hybrydowy: podobieństwo znormalizowane w puli kandydatów + pokrycie technologii z CV."""
        if not rows:
            return []
        sims = [r["semantic"] for r in rows]
        lo, hi = min(sims), max(sims)
        ranked = []
        for r in rows:
            techs = r["technologies"]
            have = sum(1 for t in techs if has_skill(t))
            coverage = have / len(techs) if techs else NEUTRAL_COVERAGE
            semantic_norm = (r["semantic"] - lo) / (hi - lo) if hi > lo else 1.0
            score = SEMANTIC_WEIGHT * semantic_norm + TECH_WEIGHT * coverage
            ranked.append({
                **r,
                "technologies": [{"name": t, "have": has_skill(t)} for t in techs],
                "coverage": {"have": have, "total": len(techs)},
                "semantic": round(float(r["semantic"]), 4),
                "match": round(score * 100),
            })
        return sorted(ranked, key=lambda m: m["match"], reverse=True)
