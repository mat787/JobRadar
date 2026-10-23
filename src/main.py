import argparse
import random
import time

from database.connection import Database
from database.init_db import init_db
from database.offer_repository import OfferRepository
from scraper.scraper import PracujScraper

BASE_URL = 'https://it.pracuj.pl/praca?sc=0'
MAX_RETRIES = 3


def page_url(pn):
    return BASE_URL if pn == 1 else f'{BASE_URL}&pn={pn}'


def fetch_with_retry(func, *args):
    """Wywołuje func; przy błędzie czeka coraz dłużej i próbuje ponownie."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func(*args)
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            pause = 30 * attempt
            print(f"  Błąd ({e}). Próba {attempt}/{MAX_RETRIES}, ponawiam za {pause} s...")
            time.sleep(pause)


def fetch_details(scraper, offers):
    """Uzupełnia szczegóły ofert; błąd pojedynczej oferty nie przerywa całości."""
    for i, offer in enumerate(offers, start=1):
        if not offer.url:
            continue
        try:
            offer.apply_details(fetch_with_retry(scraper.get_offer_details, offer.url))
        except Exception as e:
            print(f"  Pomijam szczegóły oferty {offer.url}: {e}")
        print(f"  Szczegóły {i}/{len(offers)}", end='\r')
        time.sleep(random.uniform(1.5, 3.5))


def main(max_pages):
    scraper = PracujScraper()

    with Database() as db:
        init_db(db)
        db.conn.commit()
        repo = OfferRepository(db)

        for pn in range(1, max_pages + 1):
            offers = fetch_with_retry(scraper.get_offers, page_url(pn))

            if not offers:
                print(f"Brak ofert na stronie {pn}. Kończę pobieranie.")
                break

            known = repo.ids_with_details(offer.id for offer in offers)
            to_fetch = [offer for offer in offers if offer.id not in known]
            print(f"Strona {pn}: {len(offers)} ofert, nowych do pobrania szczegółów: {len(to_fetch)}")
            fetch_details(scraper, to_fetch)

            repo.save(offers)
            db.conn.commit()
            print(f"Strona {pn} zapisana. Ofert w bazie: {repo.count()}")

            if pn % 10 == 0:
                oddech = random.uniform(15.0, 30.0)
                print(f"Paczka 10 stron pobrana. Chwila oddechu... ({oddech:.1f} s)")
                time.sleep(oddech)
            else:
                time.sleep(random.uniform(2.5, 5.5))

        print(f"Gotowe. Łącznie ofert w bazie: {repo.count()}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Pobiera oferty IT z pracuj.pl do bazy.")
    parser.add_argument('--max-pages', type=int, default=200,
                        help="maksymalna liczba stron listy ofert (domyślnie: wszystkie)")
    main(parser.parse_args().max_pages)
