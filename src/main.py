import time
import random

from scraper.scraper import PracujScraper


def main():

    wszystkie_oferty = []

    for pn in range(1, 100):
        url = f'https://it.pracuj.pl/praca?pn={pn}'
        scraper = PracujScraper(url)

        nowe_oferty = scraper.get_offers()

        if not nowe_oferty:
            print(f"Brak ofert na stronie {pn}. Kończę pobieranie.")
            break

        wszystkie_oferty.extend(nowe_oferty)
        print(f"Pobrano {len(nowe_oferty)} ofert ze strony {pn}...")

        if pn % 10 == 0:
            oddech = random.uniform(15.0, 30.0)
            print(f"Paczka 10 stron pobrana. Chwila oddechu... ({oddech:.1f} s)")
            time.sleep(oddech)
        else:
            przerwa = random.uniform(2.5, 5.5)
            time.sleep(przerwa)

    print(f"Łącznie zebrano: {len(wszystkie_oferty)} ofert.")

    for oferta in wszystkie_oferty:



if __name__ == '__main__':
    main()