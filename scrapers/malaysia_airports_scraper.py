"""
Malaysia Airports — KLIA2 Arrivals Scraper  (SPARK agent data source)
=====================================================================

Scrapes live KLIA2 arrival flights from https://www.klia2.info/flight/arrival/

Returns a normalised list of flight dicts:
    {
      "flight_number": "AK717",
      "origin_city":   "Bangkok",
      "origin_code":   "BKK",
      "scheduled":     "07:10",
      "actual":        "07:10",
      "delay_minutes": 0,
      "airline":       "AirAsia",
      "status":        "Landed",      # On Time | Delayed | Landed | Cancelled
    }

DESIGN NOTE (verified June 2026)
--------------------------------
The klia2.info arrivals board is rendered client-side (the flight rows are not
present in the initial HTML response) and the host aggressively drops rapid
connections. A pure-HTML scrape therefore returns nothing most of the time.

This module still makes a genuine fetch + parse attempt — it handles the case
where a server-rendered <table> IS present, tolerating several column layouts —
but it is built to FAIL SOFT: any network/parse problem returns an empty list
so the caller falls back to the Flights tab in Google Sheets. The Airport Queue
tab shows a LIVE badge when this returns rows and a SIMULATED badge when it
falls back. Swapping in AviationStack (production) only changes this file.
"""

import re
import time

try:
    import requests
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    requests = None
    BeautifulSoup = None

ARRIVALS_URL = "https://www.klia2.info/flight/arrival/"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Map common IATA airline prefixes -> airline name (used to infer aircraft type
# downstream when the source does not state it explicitly).
_AIRLINE_BY_PREFIX = {
    "AK": "AirAsia",
    "D7": "AirAsia X",
    "FD": "Thai AirAsia",
    "QZ": "Indonesia AirAsia",
    "MH": "Malaysia Airlines",
    "OD": "Batik Air Malaysia",
    "FY": "Firefly",
    "ID": "Batik Air",
}


def _airline_from_flight(flight_no):
    return _AIRLINE_BY_PREFIX.get((flight_no or "")[:2].upper(), "")


def _to_minutes(hhmm):
    m = re.match(r"^\s*(\d{1,2}):(\d{2})", hhmm or "")
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def _delay(scheduled, actual):
    s, a = _to_minutes(scheduled), _to_minutes(actual)
    if s is None or a is None:
        return 0
    d = a - s
    # handle midnight wrap (e.g. sched 23:50, actual 00:10)
    if d < -720:
        d += 1440
    return d


def _status_from(text, delay_minutes):
    t = (text or "").lower()
    if "cancel" in t:
        return "Cancelled"
    if "land" in t or "arriv" in t:
        return "Landed"
    if "delay" in t or delay_minutes > 0:
        return "Delayed"
    return "On Time"


def _parse_table_rows(soup):
    """Best-effort parse of any arrivals <table> into flight dicts."""
    flights = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        for tr in rows[1:]:
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) < 3:
                continue
            # Heuristic: find the cell that looks like a flight number.
            flight_no = next(
                (c for c in cells if re.match(r"^[A-Z]{2}\d{2,4}$", c.replace(" ", ""))),
                None,
            )
            if not flight_no:
                continue
            flight_no = flight_no.replace(" ", "")
            times = [c for c in cells if re.match(r"^\d{1,2}:\d{2}", c)]
            scheduled = times[0] if times else ""
            actual = times[1] if len(times) > 1 else scheduled
            # origin = longest alpha cell that isn't the flight no / status
            origin = ""
            for c in cells:
                if c == flight_no:
                    continue
                if re.search(r"[A-Za-z]{4,}", c) and not re.match(r"^\d", c):
                    origin = c
                    break
            code_m = re.search(r"\b([A-Z]{3})\b", " ".join(cells))
            delay = _delay(scheduled, actual)
            flights.append({
                "flight_number": flight_no,
                "origin_city": origin,
                "origin_code": code_m.group(1) if code_m else "",
                "scheduled": scheduled,
                "actual": actual,
                "delay_minutes": delay,
                "airline": _airline_from_flight(flight_no),
                "status": _status_from(" ".join(cells), delay),
            })
    return flights


def scrape_klia2_arrivals(timeout=8, retries=2):
    """
    Attempt to fetch + parse live KLIA2 arrivals.
    Returns a list of flight dicts, or [] on any failure (fail-soft).
    """
    if requests is None or BeautifulSoup is None:
        return []
    for attempt in range(retries):
        try:
            resp = requests.get(ARRIVALS_URL, headers=_HEADERS, timeout=timeout)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            flights = _parse_table_rows(soup)
            if flights:
                return flights
            # No server-rendered table (page is JS-rendered) -> fall through.
            return []
        except Exception:
            if attempt < retries - 1:
                time.sleep(1.0)
            continue
    return []


def is_live():
    """True when the scraper currently returns at least one flight."""
    return len(scrape_klia2_arrivals()) > 0


if __name__ == "__main__":
    print(f"Fetching {ARRIVALS_URL} ...")
    data = scrape_klia2_arrivals()
    if data:
        print(f"LIVE: {len(data)} arrivals scraped")
        for f in data[:10]:
            print(" ", f)
    else:
        print("NO LIVE DATA (page is JS-rendered / host blocked the request).")
        print("Caller will fall back to the Flights tab in Google Sheets.")
