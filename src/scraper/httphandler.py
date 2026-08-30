import httpx
import requests
from curl_cffi import requests

class httpHandler:
    def __init__(self, url):
        self.url = url

    def send_request(self):
        r = requests.get(
            'https://it.pracuj.pl/praca',
            impersonate="chrome120",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
            }
        )
        return r.status_code, r.text



if __name__ == '__main__':
    pracuj = httpHandler('https://it.pracuj.pl/praca')
    status, tekst = pracuj.send_request()
    print("Test scrapera:", status)
