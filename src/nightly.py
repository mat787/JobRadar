import argparse
import contextlib
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from database.connection import Database
from database.offer_repository import OfferRepository
from fill_details import fill_details
from main import main as scrape
from llm.chat import ChatClient
from llm.embedder import Embedder
from rag.indexer import index_offers
from rag.service import RagService

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOCK_FILE = LOG_DIR / "nightly.lock"
STALE_LOCK_HOURS = 12
FULL_RUN_WEEKDAY = 6
TOP_ANALYSES = 20
ANALYSIS_LEVEL = 'junior'


class Tee:
    """Pisze jednocześnie na ekran i do pliku z logiem."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            stream.write(text)
        return len(text)

    def flush(self):
        for stream in self.streams:
            stream.flush()


@contextlib.contextmanager
def single_run_lock():
    """Nie pozwala uruchomić dwóch przebiegów naraz; stary zamek (po awarii) jest usuwany."""
    if LOCK_FILE.exists() and time.time() - LOCK_FILE.stat().st_mtime > STALE_LOCK_HOURS * 3600:
        LOCK_FILE.unlink()
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit(f"Inny przebieg już trwa (plik {LOCK_FILE}). Kończę.")
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        LOCK_FILE.unlink(missing_ok=True)


def step(title):
    print(f"\n=== {datetime.now():%H:%M:%S}  {title} ===", flush=True)


def run(full):
    step("Sprawdzam połączenie z bazą")
    with Database() as db:
        started_at = db.conn.execute("SELECT now()").fetchone()[0]
    print("Baza działa.")

    step(f"Scrapowanie listy ofert ({'pełne' if full else 'przyrostowe'})")
    stats = scrape(200, incremental=not full)

    step("Oznaczanie nieaktywnych ofert")
    with Database() as db:
        repo = OfferRepository(db)
        expired = repo.deactivate_expired()
        unseen = repo.deactivate_unseen(started_at) if full and stats["reached_end"] else 0
        db.conn.commit()
        active = repo.count(active_only=True)
    print(f"Wygasłe: {expired}, zniknęły z listy: {unseen}, aktywnych ofert: {active}")
    if full and not stats["reached_end"]:
        print("Pełny przebieg nie doszedł do końca listy — nie oznaczam zniknięć, żeby nie wyłączyć aktywnych ofert.")

    step("Uzupełnianie brakujących szczegółów")
    fill_details()

    step("Embeddingi nowych ofert")
    try:
        index_offers()
    except Exception as e:
        print(f"Pomijam embeddingi (czy LM Studio działa z modelem embeddingów?): {e}")

    step(f"Analiza {TOP_ANALYSES} najlepiej dopasowanych ofert (Gemma)")
    analysed = 0
    try:
        with Database() as db:
            analysed = RagService(db, Embedder(), ChatClient()).analyze_top(TOP_ANALYSES, level=ANALYSIS_LEVEL)
    except Exception as e:
        print(f"Pomijam analizy (czy LM Studio działa z modelem czatu?): {e}")

    return {**stats, "expired": expired, "unseen": unseen, "active": active, "analysed": analysed}


def main():
    parser = argparse.ArgumentParser(description="Nocna aktualizacja JobRadar.")
    parser.add_argument("--full", action="store_true", help="wymuś pełne przejście listy ofert")
    args = parser.parse_args()
    full = args.full or datetime.now().weekday() == FULL_RUN_WEEKDAY

    LOG_DIR.mkdir(exist_ok=True)
    log_path = LOG_DIR / f"nightly-{datetime.now():%Y-%m-%d}.log"

    with open(log_path, "a", encoding="utf-8") as log, contextlib.redirect_stdout(Tee(sys.stdout, log)):
        print(f"\n##### JobRadar nightly, start {datetime.now():%Y-%m-%d %H:%M:%S} #####")
        try:
            with single_run_lock():
                result = run(full)
            print(f"\n##### Koniec {datetime.now():%H:%M:%S}: {result} #####")
        except SystemExit as e:
            print(e)
            raise
        except Exception:
            print("\n##### BŁĄD #####")
            traceback.print_exc(file=sys.stdout)
            raise SystemExit(1)


if __name__ == "__main__":
    main()
