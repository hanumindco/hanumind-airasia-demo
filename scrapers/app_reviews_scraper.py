"""
App Store reviews scraper — Google Play (RELAY agent / Reputation Intelligence)
==============================================================================

Pulls REAL reviews from the Google Play Store for the two AirAsia ride apps via
the free `google-play-scraper` library — no API key, no cost.

  Passenger app : com.airasia.mobile  (AirAsia MOVE)   — 50 newest, keyword-filtered
  Driver app    : com.dacsee          (airasia ride Driver) — 20 newest, unfiltered

Results cached 60 minutes. Falls back to 3 fictional reviews per app on failure.
"""

import re
import time
from datetime import datetime, timedelta

try:
    from google_play_scraper import app as gp_app, reviews as gp_reviews, Sort
except Exception:  # pragma: no cover
    gp_app = gp_reviews = Sort = None

PASSENGER_ID = "com.airasia.mobile"
DRIVER_ID = "com.dacsee"

# Whole-word matching only. "fare" and "car" are dropped entirely (too generic —
# they match flight fares / "credit card"). \b boundaries stop "ride" matching inside
# "provide" / "stride".
RIDE_RE = re.compile(
    r"\bride\b|\bdriver\b|\bpickup\b|\bpick up\b|\be-hailing\b|\bbooked ride\b",
    re.IGNORECASE,
)


def _is_ride_related(text):
    return bool(RIDE_RE.search(text or ""))


def _recent_negative(reviews, days=7):
    """Count negative reviews (1-3 stars) dated within the last `days` days."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return sum(1 for r in reviews
               if int(r.get("score") or 0) <= 3 and str(r.get("date") or "") >= cutoff)

_cache = {"data": None, "ts": 0.0}
_TTL = 3600  # 60 minutes

PASSENGER_FALLBACK = {
    "rating": 3.7, "total": 30000, "live": False,
    "reviews": [
        {"score": 2, "date": "2026-06-10", "user": "Aiman R.", "text": "Booked a ride to KLIA2 and the driver cancelled twice. Fare estimate was off too."},
        {"score": 4, "date": "2026-06-09", "user": "Mei Ling", "text": "Driver arrived on time for my airport pickup, smooth ride. App could be a bit faster."},
        {"score": 1, "date": "2026-06-08", "user": "Ravi K.", "text": "E-hailing pickup never showed up, waited 30 minutes. Very disappointed."},
    ],
}
DRIVER_FALLBACK = {
    "rating": 3.7, "total": 1400, "live": False,
    "reviews": [
        {"score": 5, "date": "2026-06-04", "user": "Hafiz", "text": "Lowest platform fee and easy to get airport jobs. Best driver app so far."},
        {"score": 2, "date": "2026-06-02", "user": "Suresh", "text": "App keeps freezing during trips. Needs proper bug fixes."},
        {"score": 3, "date": "2026-05-30", "user": "Lim", "text": "Decent earnings but the airport queue system at KLIA2 needs work."},
    ],
}


def _normalise(r):
    return {
        "score": int(r.get("score") or 0),
        "date": str(r.get("at") or "")[:10],
        "user": (r.get("userName") or "Anonymous").strip() or "Anonymous",
        "text": (r.get("content") or "").strip(),
    }


def _fetch_app(app_id, count, keyword_filter):
    info = gp_app(app_id, lang="en", country="my")
    rows, _ = gp_reviews(app_id, lang="en", country="my", sort=Sort.NEWEST, count=count)
    revs = [_normalise(r) for r in rows if (r.get("content") or "").strip()]
    if keyword_filter:
        revs = [v for v in revs if _is_ride_related(v["text"])]
    return {
        "rating": round(float(info.get("score") or 0), 2),
        "total": int(info.get("reviews") or 0),
        "title": info.get("title", ""),
        "reviews": revs,
        "live": True,
    }


def get_app_reviews(force=False):
    """Return {passenger:{...}, driver:{...}}. Cached 60 min; fails soft to fixtures."""
    now = time.time()
    if not force and _cache["data"] is not None and (now - _cache["ts"]) < _TTL:
        return _cache["data"]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out = {}
    if gp_app is not None:
        try:
            p = _fetch_app(PASSENGER_ID, 50, keyword_filter=True)
            # Real ride-related negative complaints (1-3 stars) in last 7 days — for the
            # Nerve KPI card. Computed from the GENUINE filtered list, even if we fall back.
            ride_neg_7d = _recent_negative(p["reviews"], 7)
            if len(p["reviews"]) < 3:
                # Genuine ride-service reviews are too sparse in the latest 50 (MOVE is a
                # flights/hotels superapp) — show ride-specific fixtures instead of flight
                # complaints, but keep the app's REAL overall rating + total count.
                fb = dict(PASSENGER_FALLBACK)
                fb["reviews"] = list(PASSENGER_FALLBACK["reviews"])
                fb["rating"], fb["total"], fb["live"] = p["rating"], p["total"], False
                fb["ride_negative_7d"] = ride_neg_7d
                out["passenger"] = fb
                print(f"[{ts}] app_reviews: passenger {len(p['reviews'])} ride reviews after filter — using ride fixtures")
            else:
                p["ride_negative_7d"] = ride_neg_7d
                out["passenger"] = p
                print(f"[{ts}] app_reviews: passenger LIVE — {len(p['reviews'])} ride-related of 50")
        except Exception as e:  # noqa: BLE001
            fb = dict(PASSENGER_FALLBACK); fb["ride_negative_7d"] = 0
            out["passenger"] = fb
            print(f"[{ts}] app_reviews: passenger fallback ({e})")
        try:
            drv = _fetch_app(DRIVER_ID, 20, keyword_filter=False)
            drv["negative_7d"] = _recent_negative(drv["reviews"], 7)
            out["driver"] = drv
            print(f"[{ts}] app_reviews: driver LIVE — {len(drv['reviews'])} reviews, {drv['negative_7d']} negative this week")
        except Exception as e:  # noqa: BLE001
            fb = dict(DRIVER_FALLBACK); fb["negative_7d"] = _recent_negative(DRIVER_FALLBACK["reviews"], 7)
            out["driver"] = fb
            print(f"[{ts}] app_reviews: driver fallback ({e})")
    else:
        pf = dict(PASSENGER_FALLBACK); pf["ride_negative_7d"] = 0
        df = dict(DRIVER_FALLBACK); df["negative_7d"] = _recent_negative(DRIVER_FALLBACK["reviews"], 7)
        out = {"passenger": pf, "driver": df}
        print(f"[{ts}] app_reviews: library unavailable — using fixtures")
    _cache.update(data=out, ts=now)
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(get_app_reviews(force=True), indent=1, default=str)[:1500])
