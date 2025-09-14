import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib.robotparser

class Scraper:
    def __init__(self, url, rate_limit=1.0, respect_robots=True, headers=None):
        """
        :param url: Target URL
        :param rate_limit: Minimum seconds between requests
        :param respect_robots: Whether to check robots.txt
        :param headers: Custom headers (default: basic User-Agent)
        """
        self.url = url
        self.rate_limit = rate_limit
        self.respect_robots = respect_robots
        self.last_request = 0
        self.headers = headers or {"User-Agent": "scrape_eazy/0.1"}
        self.soup = None

        if respect_robots:
            self._check_robots()

        self._fetch()

    def _check_robots(self):
        parsed = requests.utils.urlparse(self.url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
            if not rp.can_fetch(self.headers["User-Agent"], self.url):
                raise PermissionError(f"❌ Scraping disallowed by robots.txt: {self.url}")
        except Exception:
            # Fail open if robots.txt not available
            pass

    def _fetch(self):
        now = time.time()
        if now - self.last_request < self.rate_limit:
            time.sleep(self.rate_limit - (now - self.last_request))
        r = requests.get(self.url, headers=self.headers)
        r.raise_for_status()
        self.last_request = time.time()
        self.soup = BeautifulSoup(r.text, "html.parser")

    def select(self, selector):
        return self.soup.select(selector)

    def text(self, selector):
        return [el.get_text(strip=True) for el in self.soup.select(selector)]

    def attr(self, selector, attr):
        return [el.get(attr) for el in self.soup.select(selector) if el.has_attr(attr)]
