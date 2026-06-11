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
from datetime import datetime

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


# ═══════════════════════════════════════════════════════════════════════════════
# REAL KLIA2 ARRIVALS — Malaysia Airports official FIDS feed
# ═══════════════════════════════════════════════════════════════════════════════
# The malaysiaairports.com.my arrivals page is a JS-rendered Next.js app — its
# flight rows come from this public FIDS JSON endpoint (the same one every browser
# on that site calls). FIDS_KEY is the PUBLIC x-api-key embedded in their frontend:
# free, no signup, no rate limit, no cost — NOT a paid API and NOT a Railway env
# var. This is the reliable equivalent of "scraping the Malaysia Airports website".
#
# get_klia2_arrivals() serves live data to the dashboard when available and FALLS
# BACK to the stable Flights Google Sheet on any failure. It does NOT write to the
# Sheet — the Flights tab is the curated demo source of truth. Use the on-demand
# sync_to_flights_sheet() only if you deliberately want to snapshot live data.

FIDS_URL = "https://api.myairports.com.my/passenger-fids/api/flights/search-flights"
FIDS_KEY = "f02f252a781a4db584d1ae9fce22bed1"   # public key from the official site frontend
FIDS_LOAD_FACTOR = 0.84
_DEFAULT_NARROWBODY = 160

# operator code -> (aircraft type, seats)
_FIDS_FLEET = {
    "AK": ("A320-200", 180), "FD": ("A320-200", 180), "QZ": ("A320-200", 180),
    "I5": ("A320-200", 180), "Z2": ("A320-200", 180), "5J": ("A320-200", 180),
    "D7": ("A330-300", 377), "XJ": ("A330-300", 377), "XT": ("A330-300", 377),
    "MH": ("B737-800", 162), "OD": ("B737-800", 162), "ID": ("B737-800", 162),
    "FY": ("ATR 72-500", 72),
}
_FIDS_SEATS = {"A320-200": 180, "A321neo": 236, "A330-300": 377, "B737-800": 162,
               "B737 MAX 8": 189, "B737-900ER": 180, "ATR 72-500": 72}

_arrivals_cache = {"data": None, "ts": 0.0}
_ARRIVALS_TTL = 1800  # 30 minutes
_last_source = {"source": None}   # "live" | "sheet" — set by get_klia2_arrivals()


def _fids_aircraft(flight_no, airline_name):
    op = (flight_no or "")[:2].upper()
    if op in _FIDS_FLEET:
        return _FIDS_FLEET[op]
    if "ASIA X" in (airline_name or "").upper():
        return ("A330-300", 377)
    return ("Narrowbody", _DEFAULT_NARROWBODY)


def _fids_dt(x):
    try:
        return datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _fids_delay(scheduled, actual):
    a, s = _fids_dt(actual), _fids_dt(scheduled)
    if not a or not s:
        return 0
    return int((a - s).total_seconds() // 60)


def _fids_status(status_code, status, delay):
    s = (status or "").upper()
    c = (status_code or "").upper()
    if "CANCEL" in s or c in ("CNL", "CNX"):
        return "Cancelled"
    if "DELAY" in s or c == "FDL":
        return "Delayed"
    if any(k in s for k in ("BAG", "LANDED", "ARRIVED", "OPEN")) or c in ("COP", "CFB", "CLB", "LND", "ARR"):
        return "Landed"
    return "Delayed" if delay > 0 else "On Time"


def _normalise_fids(f):
    """Map one raw FIDS flight record to the normalised dashboard shape."""
    try:
        fn = (f.get("flightNumber") or "").replace(" ", "")
        if not fn:
            return None
        airline = (f.get("name") or "").title()
        origin = f.get("origin") or {}
        sched = f.get("scheduledTime") or ""
        actual = f.get("flightTime") or f.get("updatedTime") or sched
        delay = _fids_delay(sched, actual)
        aircraft, seats = _fids_aircraft(fn, airline)
        pax = round(seats * FIDS_LOAD_FACTOR)
        return {
            "flight_number": fn,
            "airline": airline,
            "origin_city": (origin.get("city") or "").split("(")[0].strip().title(),
            "origin_code": origin.get("code") or "",
            "scheduled": sched[11:16],
            "actual": actual[11:16],
            "delay_minutes": delay,
            "aircraft_type": aircraft,
            "seats": seats,
            "passenger_estimate": pax,
            "passenger_count": pax,           # load-factor estimate (no live pax count in feed)
            "status": _fids_status(f.get("statusCode"), f.get("status"), delay),
        }
    except Exception:
        return None


def get_klia2_arrivals(force=False, take=60):
    """
    Return real KLIA2 arrivals from the Malaysia Airports FIDS feed.
    Cached for 30 minutes. Falls back to the Flights Google Sheet on any failure.
    Each scrape attempt is logged to console with timestamp + result count.
    """
    now = time.time()
    if not force and _arrivals_cache["data"] is not None and (now - _arrivals_cache["ts"]) < _ARRIVALS_TTL:
        return _arrivals_cache["data"]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if requests is not None:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                "Accept": "application/json",
                "Referer": "https://www.malaysiaairports.com.my/",
                "x-api-key": FIDS_KEY,
            }
            params = {"code": "A", "key": "all", "terminal": "KLIA2", "dayKey": "0",
                      "live": "true", "skip": "0", "take": str(take), "value": ""}
            r = requests.get(FIDS_URL, headers=headers, params=params, timeout=12)
            rows = r.json().get("flightStatuses", []) if r.status_code == 200 else []
            flights = [x for x in (_normalise_fids(f) for f in rows) if x]
            if flights:
                _arrivals_cache.update(data=flights, ts=now)
                _last_source["source"] = "live"
                print(f"[{ts}] malaysia_airports_scraper: LIVE {len(flights)} KLIA2 arrivals")
                return flights
            print(f"[{ts}] malaysia_airports_scraper: 0 live rows (HTTP {r.status_code}) — falling back to Sheet")
        except Exception as e:  # noqa: BLE001
            print(f"[{ts}] malaysia_airports_scraper: ERROR {e} — falling back to Sheet")
    fb = _sheet_fallback()
    _arrivals_cache.update(data=fb, ts=now)
    _last_source["source"] = "sheet"
    return fb


def _sheet_fallback():
    """Read the stable curated Flights Google Sheet into the normalised shape."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        from sheets.sheets_client import get_flights
        out = []
        for r in get_flights():
            aircraft = (r.get("Aircraft Type") or "").strip() or "Narrowbody"
            seats = _FIDS_SEATS.get(aircraft, _DEFAULT_NARROWBODY)
            try:
                delay = int(float(str(r.get("Delay (minutes)", "0") or 0)))
            except Exception:
                delay = 0
            try:
                pax = int(float(str(r.get("Passenger Count", "") or 0))) or round(seats * FIDS_LOAD_FACTOR)
            except Exception:
                pax = round(seats * FIDS_LOAD_FACTOR)
            out.append({
                "flight_number": r.get("Flight Number", ""),
                "airline": r.get("Airline", ""),
                "origin_city": r.get("Origin City", ""),
                "origin_code": r.get("Origin Airport Code", ""),
                "scheduled": r.get("Scheduled Arrival Time", ""),
                "actual": r.get("Actual Arrival Time", ""),
                "delay_minutes": delay,
                "aircraft_type": aircraft,
                "seats": seats,
                "passenger_estimate": round(seats * FIDS_LOAD_FACTOR),
                "passenger_count": pax,
                "status": "On Time" if delay <= 0 else "Delayed",
            })
        print(f"[{ts}] malaysia_airports_scraper: SHEET fallback {len(out)} flights")
        return out
    except Exception as e:  # noqa: BLE001
        print(f"[{ts}] malaysia_airports_scraper: sheet fallback failed ({e})")
        return []


def sync_to_flights_sheet():
    """
    MANUAL / ON-DEMAND ONLY. Snapshot the current live FIDS arrivals into the
    Flights Google Sheet. NOT called by any scheduler — the Flights tab is the
    stable curated demo source. Overwrites existing Flights data rows; call only
    when you deliberately want a live snapshot. Returns the number of rows written.
    """
    flights = get_klia2_arrivals(force=True)
    if not flights:
        print("sync_to_flights_sheet: no live flights to write")
        return 0
    try:
        from sheets.sheets_client import get_sheet
        from gspread.utils import rowcol_to_a1
        ws = get_sheet("Flights")
        headers = ws.row_values(1)

        def col(name):
            return headers.index(name) + 1 if name in headers else None

        def cell(f, name):
            m = {
                "Flight Number": f["flight_number"], "Origin City": f["origin_city"],
                "Origin Airport Code": f["origin_code"], "Scheduled Arrival Time": f["scheduled"],
                "Actual Arrival Time": f["actual"], "Delay (minutes)": f["delay_minutes"],
                "Passenger Count": f["passenger_count"], "Data Source": "Malaysia Airports Live",
                "Airline": f["airline"], "Aircraft Type": f["aircraft_type"],
            }
            return m.get(name, "")

        n = len(flights)
        existing_rows = len(ws.get_all_values()) - 1
        rows = [[cell(f, h) for h in headers] for f in flights]
        ws.update(values=rows, range_name=f"A2:{rowcol_to_a1(n + 1, len(headers))}",
                  value_input_option="RAW")
        # clear any leftover old rows beyond the new data
        if existing_rows > n:
            blanks = [["" for _ in headers] for _ in range(existing_rows - n)]
            ws.update(values=blanks,
                      range_name=f"A{n + 2}:{rowcol_to_a1(existing_rows + 1, len(headers))}",
                      value_input_option="RAW")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] sync_to_flights_sheet: wrote {n} live flights to Flights tab")
        return n
    except Exception as e:  # noqa: BLE001
        print(f"sync_to_flights_sheet: failed ({e})")
        return 0


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
