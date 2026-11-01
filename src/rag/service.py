from concurrent.futures import ThreadPoolExecutor

from psycopg.rows import dict_row

from database.analysis_repository import AnalysisRepository
from rag.analyzer import PROMPT_VERSION, MatchAnalyzer
from rag.retriever import OfferRetriever
from user.profile import commercial_months, cv_hash, load_cv_text

ANALYSIS_COLUMNS = "id, title, company, technologies, requirements, nice_to_have, about_project"


class RagService:
    """Jedno wejście do RAG-a dla API i nocnego skryptu.

    Zależności (baza, embedder, czat) przychodzą z zewnątrz — w testach albo na GCP podstawia się inne.
    """

    def __init__(self, db, embedder, chat=None):
        self.db = db
        self.retriever = OfferRetriever(db, embedder)
        self.analyzer = MatchAnalyzer(chat) if chat else None
        self.analyses = AnalysisRepository(db)
        self.cv_text = load_cv_text()
        self.cv_hash = cv_hash(self.cv_text)

    def match_profile(self, *, level=None, limit=20):
        """Oferty najlepiej pasujące do CV (szybko, bez LLM) + wynik analizy, jeśli już jest w cache."""
        matches = self.retriever.search(self.cv_text, level=level, limit=limit)
        scores = self.analyses.scores([m["id"] for m in matches], self.cv_hash, PROMPT_VERSION)
        matches = [{**m, "analysis_score": scores.get(m["id"])} for m in matches]
        # Oferty z analizą AI (dokładniejszą niż podobieństwo wektorów) najpierw, według jej wyniku
        return sorted(matches, key=lambda m: (m["analysis_score"] is not None, m["analysis_score"] or m["match"]), reverse=True)

    def search(self, text, *, level=None, limit=30):
        return self.retriever.search(text, level=level, limit=limit)

    def cached_analysis(self, offer_id):
        return self.analyses.get(offer_id, self.cv_hash, PROMPT_VERSION)

    def analyze_offer(self, offer_id, force=False):
        """Analiza jednej oferty: z cache albo liczona teraz przez LLM."""
        if not force and (cached := self.cached_analysis(offer_id)):
            return cached
        row = self._offer_rows([offer_id])
        if not row:
            return None
        self._require_analyzer()
        result = self.analyzer.analyze(self.cv_text, commercial_months(), row[0])
        self.analyses.save(offer_id, self.cv_hash, PROMPT_VERSION, result)
        self.db.conn.commit()
        return self.cached_analysis(offer_id)

    def analyze_top(self, n=20, workers=4, level=None):
        """Analizuje najlepiej dopasowane oferty, których nie ma jeszcze w cache (kilka naraz)."""
        self._require_analyzer()
        top = self.retriever.search(self.cv_text, level=level, limit=n)
        done = self.analyses.analysed_ids([m["id"] for m in top], self.cv_hash, PROMPT_VERSION)
        todo = self._offer_rows([m["id"] for m in top if m["id"] not in done])
        todo = [r for r in todo if r["requirements"]]
        months = commercial_months()
        print(f"Do analizy: {len(todo)} ofert (w cache: {len(done)})")

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(self.analyzer.analyze, self.cv_text, months, row): row for row in todo}
            for future, row in futures.items():
                try:
                    result = future.result()
                except Exception as e:
                    print(f"  Błąd analizy „{row['title']}”: {e}")
                    continue
                self.analyses.save(row["id"], self.cv_hash, PROMPT_VERSION, result)
                self.db.conn.commit()
                print(f"  {result['score']:>3}  {row['title'][:60]}  ({result['duration_ms'] / 1000:.1f} s)")
        return len(todo)

    def _offer_rows(self, ids):
        if not ids:
            return []
        with self.db.conn.cursor(row_factory=dict_row) as cur:
            return cur.execute(f"SELECT {ANALYSIS_COLUMNS} FROM offers WHERE id = ANY(%s)", (list(ids),)).fetchall()

    def _require_analyzer(self):
        if not self.analyzer:
            raise RuntimeError("RagService utworzony bez ChatClient — analiza LLM niedostępna.")
