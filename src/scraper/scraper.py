from httphandler import httpHandler

from bs4 import BeautifulSoup
import json

moj_klient = httpHandler('https://it.pracuj.pl/praca')
status, html_text = moj_klient.send_request()

if status == 200:
    soup = BeautifulSoup(html_text, 'html.parser')
    script_tag = soup.find('script', id='__NEXT_DATA__')

    if script_tag:
        dane_slownik = json.loads(script_tag.text)
        queries = dane_slownik['props']['pageProps']['dehydratedState']['queries']

        with open('data.json', 'w', encoding='utf-8') as file:
            json.dump(queries, file, indent=4)

        for query in queries:

            data_dict = query.get('state', {}).get('data', {})

            # Sprawdzamy, czy to jest TA paczka (czy ma klucz groupedOffers)
            if isinstance(data_dict, dict) and 'groupedOffers' in data_dict:
                offers = data_dict['groupedOffers']
                print(f"BINGO! Znaleziono {len(offers)} ofert na tej stronie.")

                for offer in offers:
                    print("Technologie:", offer.get('technologies'))
                    print("Stanowisko:", offer.get('jobTitle'))
                    print("Firma:", offer.get('companyName'))

                    # --- BEZPIECZNE WYCIĄGANIE Z LISTY (ZAGNIEŻDŻENIE) ---
                    # .get('offers', []) gwarantuje, że jeśli klucza zabraknie, otrzymamy pustą listę zamiast błędu
                    sub_oferty = offer.get('offers', [])

                    # Sprawdzamy, czy lista istnieje i czy ma przynajmniej 1 element
                    if sub_oferty and len(sub_oferty) > 0:
                        pierwsza_sub_oferta = sub_oferty[0]
                        print("Partition ID:", pierwsza_sub_oferta.get('partitionId'))
                        print("Link do oferty:", pierwsza_sub_oferta.get('offerAbsoluteUri'))
                    else:
                        print("Partition ID: Brak")
                        print("Link do oferty: Brak")
                    # ---------------------------------------------------

                    print("Widełki:", offer.get('salaryDisplayText'))
                    print("Poziom:", offer.get('positionLevels'))
                    print("Umowa:", offer.get('typesOfContract'))

                    print("-" * 50)  # Ładna kreska oddzielająca oferty w konsoli
                    break  # Na razie przerywamy po pierwszej, żeby sprawdzić, czy działa
            print("Udało się! Oto klucze z Pracuj.pl:", dane_slownik.keys())
        else:
            print("Nie znaleziono tagu. Pracuj.pl mogło zmienić kod strony.")
    else:
        print(f"Błąd połączenia. Serwer zwrócił status: {status}")