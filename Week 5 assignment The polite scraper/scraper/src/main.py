"""
The polite scraper — Books to Scrape (sandbox site, built for this exact purpose).
Pipeline: classify -> fetch/cache -> discover -> extract -> normalize -> validate -> store -> report.
"""

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl, ValidationError

BASE_URL = "https://books.toscrape.com/"
START_URL = urljoin(BASE_URL, "catalogue/page-1.html")
MAX_CATALOGUE_PAGES = 3

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/tejaspawar7720/FlyRank-AI-Assingments)"
TIMEOUT_SECONDS = 10
POLITE_DELAY_SECONDS = 0.5

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # scraper/
CACHE_DIR = os.path.join(HERE, "cache")
OUTPUT_DIR = os.path.join(HERE, "output")

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

# run counters
run_stats = {
    "pages_fetched": 0,
    "cache_hits": 0,
    "failed_pages": 0,
}


# ---------- stage 1: fetch once, cache once ----------
def cache_path_for(url: str) -> str:
    digest = hashlib.sha1(url.encode()).hexdigest()[:12]
    return os.path.join(CACHE_DIR, f"{digest}.html")


def fetch(url: str, retries: int = 1) -> str | None:
    """Return HTML for url, using the on-disk cache. Returns None if the page could not be fetched."""
    path = cache_path_for(url)

    if os.path.exists(path):
        run_stats["cache_hits"] += 1
        print(f"CACHE HIT {url}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    for attempt in range(retries + 1):
        try:
            resp = session.get(url, timeout=TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            if attempt < retries:
                time.sleep(1)
                continue
            print(f"FAILED {url} ({exc})")
            run_stats["failed_pages"] += 1
            return None

        if resp.status_code == 200:
            resp.encoding = "utf-8"  # force correct decoding; avoids "£" -> "Â£" mojibake
            with open(path, "w", encoding="utf-8") as f:
                f.write(resp.text)
            run_stats["pages_fetched"] += 1
            print(f"FETCH {url} ({len(resp.text)} bytes)")
            time.sleep(POLITE_DELAY_SECONDS)  # only real network hits wait
            return resp.text

        if resp.status_code in (404, 403):
            # don't retry: the page won't exist tomorrow either, and 403 means "no"
            print(f"FAILED {url} (status {resp.status_code})")
            run_stats["failed_pages"] += 1
            return None

        if resp.status_code >= 500 and attempt < retries:
            time.sleep(1)
            continue

        print(f"FAILED {url} (status {resp.status_code})")
        run_stats["failed_pages"] += 1
        return None

    return None


# ---------- stage 2: discover the three catalogue pages ----------
def discover_book_urls() -> list[str]:
    urls: list[str] = []
    seen = set()
    page_url = START_URL

    for _ in range(MAX_CATALOGUE_PAGES):
        html = fetch(page_url)
        if html is None:
            break

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.select("h3 > a"):
            href = a.get("href")
            absolute = urljoin(page_url, href)
            if absolute not in seen:
                seen.add(absolute)
                urls.append(absolute)

        next_link = soup.select_one("li.next > a")
        if not next_link:
            break
        page_url = urljoin(page_url, next_link.get("href"))

    return urls


# ---------- stage 3: extract raw fields from a book page ----------
def extract_raw_record(detail_url: str, source_page: str) -> dict | None:
    html = fetch(detail_url)
    if html is None:
        return None

    soup = BeautifulSoup(html, "html.parser")
    product = soup.select_one("div.product_main")

    title = product.select_one("h1").get_text(strip=True)
    price_text = product.select_one("p.price_color").get_text(strip=True)
    availability_text = product.select_one("p.availability").get_text(strip=True)

    rating_tag = product.select_one("p.star-rating")
    rating_text = None
    if rating_tag:
        classes = rating_tag.get("class", [])
        rating_text = next((c for c in classes if c != "star-rating"), None)

    desc_heading = soup.select_one("#product_description")
    description = None
    if desc_heading:
        desc_p = desc_heading.find_next_sibling("p")
        if desc_p:
            description = desc_p.get_text(strip=True)

    return {
        "title": title,
        "product_url": detail_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


# ---------- stage 4: normalize + validate ----------
class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str | None = None
    description: str | None = None
    source_page: str
    fetched_at: str


def normalize(raw: dict) -> dict:
    # strip everything except digits and the decimal point — survives "£", "Â£",
    # or any other currency-symbol encoding glitch, not just the plain "£" case.
    digits_only = re.sub(r"[^\d.]", "", raw["price_text"])
    price_gbp = float(digits_only)
    normalized = dict(raw)
    normalized["price_gbp"] = price_gbp
    return normalized


def run():
    start = time.time()
    started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    book_urls = discover_book_urls()
    print(f"catalogue_pages={MAX_CATALOGUE_PAGES} discovered={len(book_urls)} unique_urls={len(book_urls)}")

    # to test failure handling: uncomment the next line to add a page that doesn't exist
    #book_urls.append(urljoin(BASE_URL, "catalogue/this-book-does-not-exist/index.html"))

    valid_records = {}  # keyed by canonical product_url -> dedup / idempotency
    errors = []

    for url in book_urls:
        try:
            raw = extract_raw_record(url, source_page=START_URL)
            if raw is None:
                continue  # already counted as a failed page in fetch()

            normalized = normalize(raw)
            record = BookRecord(**normalized)
            valid_records[str(record.product_url)] = json.loads(record.model_dump_json())

        except (ValidationError, ValueError, AttributeError) as exc:
            errors.append({"url": url, "reason": str(exc)})

    books = list(valid_records.values())

    with open(os.path.join(OUTPUT_DIR, "books.json"), "w", encoding="utf-8") as f:
        json.dump(books, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "errors.json"), "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2)

    report = {
        "started_at": started_at,
        "duration_seconds": round(time.time() - start, 2),
        "pages_fetched": run_stats["pages_fetched"],
        "cache_hits": run_stats["cache_hits"],
        "valid_records": len(books),
        "invalid_records": len(errors),
        "failed_pages": run_stats["failed_pages"],
    }
    with open(os.path.join(OUTPUT_DIR, "run-report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
