"""
HANUMIND MASTER — Agent Scheduler
==================================

Central scheduler for all HANUMIND agents running against the AirAsia Ride
data layer. Uses APScheduler (already in requirements.txt).

SCHEDULE OVERVIEW
-----------------
  PULSE   — Driver compliance sweep .......... DAILY at 12:01 AM  (cron)
  SPARK   — Airport queue + demand predictor .. every 30 minutes
  TOWER   — Advance-booking monitor ........... every 10 minutes
  RELAY   — Customer-support triage ........... every 15 minutes

NOTE ON PULSE (changed June 2026):
  PULSE previously ran on an interval trigger every 60 minutes. It now runs
  ONCE per day on a cron trigger at 12:01 AM. PULSE checks every driver's four
  documents (PSV, EVP, Insurance, PUSPAKOM), recomputes days-to-expiry and
  compliance status, writes results to the Drivers sheet and the
  aar_compliance_summary table, and sends WATI reminders to drivers within
  30 days of expiry. The dashboard reads those stored results all day until the
  next 12:01 AM run.

This module is safe to import: each job is wrapped so a missing/empty agent
module never crashes the scheduler. To run the scheduler as its own process:

    python scheduler.py

It is intentionally NOT started by the Flask web process (app.py) so the live
demo deploy has no extra moving parts.
"""

import logging

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
except Exception:  # pragma: no cover - apscheduler always present in requirements
    BackgroundScheduler = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [scheduler] %(message)s")
log = logging.getLogger("hanumind.scheduler")


# ---------------------------------------------------------------------------
# Job wrappers — each tries to call the real agent, but never raises.
# The agent modules live in agents/. Empty stubs are tolerated.
# ---------------------------------------------------------------------------

def _safe(name, fn):
    """Run an agent entrypoint, logging instead of crashing the scheduler."""
    try:
        log.info("running %s", name)
        result = fn()
        log.info("%s complete: %s", name, result if result is not None else "ok")
    except Exception as e:  # noqa: BLE001 - scheduler must survive any agent error
        log.warning("%s failed (non-fatal): %s", name, e)


def run_pulse():
    """Daily 12:01 AM driver-compliance sweep."""
    def _job():
        from agents import pulse  # imported lazily; tolerate empty module
        if hasattr(pulse, "run"):
            return pulse.run()
        return "pulse.run() not implemented yet — compliance read live from sheet"
    _safe("PULSE", _job)


def run_spark():
    """Airport queue + demand predictor (every 30 min)."""
    def _job():
        from agents import spark
        if hasattr(spark, "run"):
            return spark.run()
        return "spark.run() not implemented yet"
    _safe("SPARK", _job)


def run_tower():
    """Advance-booking monitor (every 10 min)."""
    def _job():
        from agents import tower
        if hasattr(tower, "run"):
            return tower.run()
        return "tower.run() not implemented yet"
    _safe("TOWER", _job)


def run_relay():
    """Customer-support triage (every 15 min)."""
    def _job():
        from agents import relay
        if hasattr(relay, "run"):
            return relay.run()
        return "relay.run() not implemented yet"
    _safe("RELAY", _job)


def run_malaysia_airports():
    """Refresh the real KLIA2 arrivals cache from the Malaysia Airports feed
    (every 30 min). Serves live data to the dashboard; does NOT write to the
    Flights Sheet — the Flights tab stays the stable curated source."""
    def _job():
        from scrapers.malaysia_airports_scraper import get_klia2_arrivals
        flights = get_klia2_arrivals(force=True)
        return f"refreshed {len(flights)} KLIA2 arrivals"
    _safe("MALAYSIA_AIRPORTS", _job)


# ---------------------------------------------------------------------------
# Scheduler assembly
# ---------------------------------------------------------------------------

def build_scheduler():
    """Construct and return a configured (but not yet started) scheduler."""
    if BackgroundScheduler is None:
        raise RuntimeError("apscheduler not installed")

    sched = BackgroundScheduler(timezone="Asia/Kuala_Lumpur")

    # PULSE — ONCE DAILY at 12:01 AM (cron). Changed from interval 60 min.
    sched.add_job(
        run_pulse,
        trigger=CronTrigger(hour=0, minute=1),
        id="pulse_daily_compliance",
        name="PULSE daily compliance sweep (12:01 AM)",
        replace_existing=True,
    )

    # SPARK — every 30 minutes
    sched.add_job(
        run_spark,
        trigger=IntervalTrigger(minutes=30),
        id="spark_airport_demand",
        name="SPARK airport queue + demand predictor",
        replace_existing=True,
    )

    # TOWER — every 10 minutes
    sched.add_job(
        run_tower,
        trigger=IntervalTrigger(minutes=10),
        id="tower_booking_monitor",
        name="TOWER advance-booking monitor",
        replace_existing=True,
    )

    # RELAY — every 15 minutes
    sched.add_job(
        run_relay,
        trigger=IntervalTrigger(minutes=15),
        id="relay_support_triage",
        name="RELAY customer-support triage",
        replace_existing=True,
    )

    # MALAYSIA AIRPORTS — refresh real KLIA2 arrivals cache every 30 minutes
    sched.add_job(
        run_malaysia_airports,
        trigger=IntervalTrigger(minutes=30),
        id="malaysia_airports_refresh",
        name="Malaysia Airports KLIA2 arrivals refresh",
        replace_existing=True,
    )

    return sched


def describe_schedule():
    """Return a human-readable summary of each job's trigger (for diagnostics)."""
    sched = build_scheduler()
    rows = []
    for job in sched.get_jobs():
        rows.append({"id": job.id, "name": job.name, "trigger": str(job.trigger)})
    return rows


if __name__ == "__main__":
    import time

    scheduler = build_scheduler()
    scheduler.start()
    log.info("scheduler started. Jobs:")
    for job in scheduler.get_jobs():
        log.info("  - %s -> %s", job.name, job.trigger)
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log.info("scheduler stopped.")
