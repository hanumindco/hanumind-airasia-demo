import os
import psycopg2
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from sheets.sheets_client import (
    get_drivers, get_bookings, get_wati_messages,
    get_flights, get_compliance_summary, read_all
)
from agents.driver_companion import ask
from agents.spark import airport_intelligence

load_dotenv('/Users/gowrishnambiar/hanumind_airasia_demo/.env')
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("landing.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/companion")
def companion():
    return render_template("companion.html")

@app.route("/api/drivers")
def api_drivers():
    return jsonify(get_drivers())

@app.route("/api/bookings")
def api_bookings():
    return jsonify(get_bookings())

@app.route("/api/wati")
def api_wati():
    return jsonify(get_wati_messages())

@app.route("/api/flights")
def api_flights():
    return jsonify(get_flights())

@app.route("/api/compliance")
def api_compliance():
    return jsonify(get_compliance_summary())

@app.route("/api/zone-demand")
def api_zone_demand():
    return jsonify(read_all("Demand — Zone Demand"))

@app.route("/api/agent-health")
def api_agent_health():
    return jsonify(read_all("System — Agent Health"))

@app.route("/api/salesforce-escalations")
def api_salesforce_escalations():
    return jsonify(read_all("CS — Salesforce Escalations"))

@app.route("/api/safety-incidents")
def api_safety_incidents():
    return jsonify(read_all("CS — Safety Incidents"))

@app.route("/api/refunds")
def api_refunds():
    return jsonify(read_all("CS — Refunds"))

@app.route("/api/driver-complaints")
def api_driver_complaints():
    return jsonify(read_all("CS — Driver Complaints"))

@app.route("/api/evp")
def api_evp():
    from datetime import datetime
    drivers = get_drivers()
    cfg = get_compliance_summary()
    c0 = cfg[0] if cfg else {}
    def _num(v, d=0):
        try:
            return int(float(str(v).replace(",", "") or d))
        except Exception:
            return d
    quota_total = _num(c0.get("EVP Quota Total"), 1000)
    def days_until(s):
        try:
            return (datetime.strptime(str(s)[:10], "%Y-%m-%d") - datetime.now()).days
        except Exception:
            return None
    table, active, inactive, cancelled = [], 0, 0, 0
    for d in drivers:
        comp = (d.get("Compliance Status") or "").strip()
        driver_status = "Inactive" if comp == "Lapsed" else "Active"
        du = days_until(d.get("EVP Expiry Date", ""))
        if du is None:
            evp_status = "Unknown"
        elif du <= 0:
            evp_status = "Expired"
        elif du <= 30:
            evp_status = "Expiring"
        else:
            evp_status = "Active"
        if driver_status == "Inactive":
            inactive += 1; colour = "red"
        elif evp_status == "Expired":
            cancelled += 1; colour = "red"
        elif evp_status == "Expiring":
            active += 1; colour = "amber"
        else:
            active += 1; colour = "green"
        table.append({
            "driver_id": d.get("Driver ID"), "name": d.get("Driver Name"),
            "evp_number": d.get("EVP Number", ""), "evp_expiry": d.get("EVP Expiry Date", ""),
            "days_until_expiry": du, "driver_status": driver_status,
            "evp_status": evp_status, "colour": colour,
        })
    available = quota_total - active - inactive - cancelled
    return jsonify({
        "quota_total": quota_total, "assigned_active": active, "assigned_inactive": inactive,
        "cancelled": cancelled, "available": available,
        "last_purchase": c0.get("EVP Last Purchase Date", ""),
        "notes": c0.get("EVP Quota Notes", ""), "drivers": table,
    })

@app.route("/api/onboarding")
def api_onboarding():
    return jsonify(read_all("Driver Onboarding"))

@app.route("/api/app-reviews")
def api_app_reviews():
    try:
        from scrapers.app_reviews_scraper import get_app_reviews
        return jsonify(get_app_reviews())
    except Exception as e:
        print(f"app-reviews error: {e}")
        return jsonify({"passenger": {"reviews": []}, "driver": {"reviews": []}})

def _rm(v):
    try:
        return int(float(str(v).replace(",", "") or 0))
    except Exception:
        return 0

@app.route("/api/incentives")
def api_incentives():
    rows = read_all("Incentive & Fraud")
    eligible = [r for r in rows if r.get("Incentive Status") in ("Eligible", "Paid", "Pending")]
    disq = [r for r in rows if r.get("Incentive Status") == "Disqualified"]
    paid = [r for r in rows if r.get("Incentive Status") == "Paid"]
    return jsonify({
        "rows": rows,
        "eligible_count": len(eligible),
        "total_payout": sum(_rm(r.get("Bonus Amount RM")) for r in eligible),
        "disqualified_count": len(disq),
        "disqualified_amount": sum(_rm(r.get("Bonus Amount RM")) for r in disq),
        "paid_count": len(paid),
    })

@app.route("/api/referrals")
def api_referrals():
    rows = read_all("Incentive & Fraud - Referrals")
    return jsonify({
        "rows": rows, "total": len(rows),
        "paid": len([r for r in rows if r.get("Payment Status") == "Paid"]),
        "pending": len([r for r in rows if r.get("Payment Status") == "Pending"]),
        "disqualified": len([r for r in rows if r.get("Payment Status") == "Disqualified"]),
    })

@app.route("/api/fraud")
def api_fraud():
    import math
    from collections import defaultdict
    KLIA2 = (2.7456, 101.7072)
    def hav(a, b, c, d):
        R = 6371; p = math.pi / 180
        x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
        return 2 * R * math.asin(math.sqrt(x))
    drivers = get_drivers()
    gps = []
    for dd in drivers:
        if dd.get("GPS Fraud Flag") == "Yes":
            try:
                lat = float(dd.get("GPS Latitude")); lng = float(dd.get("GPS Longitude"))
                dist = round(hav(KLIA2[0], KLIA2[1], lat, lng), 1)
            except Exception:
                lat = lng = dist = None
            gps.append({"driver_id": dd.get("Driver ID"), "name": dd.get("Driver Name"),
                        "queue_type": dd.get("queue_type"), "gps_lat": lat, "gps_lng": lng,
                        "distance_km": dist})
    incfraud = read_all("Incentive & Fraud - Fraud")
    # early no-show from Bookings (Control Tower no-show log); flag drivers with > 2 this month
    noshow = defaultdict(list)
    for b in get_bookings():
        if b.get("Booking Status") == "No Show" and b.get("Driver Name"):
            noshow[b.get("Driver Name")].append({"id": b.get("Booking ID"), "pickup": b.get("Pickup Time"),
                                                 "flight": b.get("Flight Number", "")})
    incidents = [{"driver": k, "count": len(v), "bookings": v} for k, v in noshow.items()]
    early = [x for x in incidents if x["count"] > 2]
    inc = read_all("Incentive & Fraud")
    disq_amount = sum(_rm(r.get("Bonus Amount RM")) for r in inc if r.get("Incentive Status") == "Disqualified")
    return jsonify({
        "gps_fraud": gps, "incentive_fraud": incfraud,
        "early_noshow": early, "noshow_incidents": incidents,
        "gps_count": len(gps), "incentive_count": len(incfraud), "early_count": len(early),
        "total_disqualified_rm": disq_amount,
    })

@app.route("/api/airport-queue")
def api_airport_queue():
    try:
        data = airport_intelligence()
        _maybe_write_airport_alert(data)
        return jsonify(data)
    except Exception as e:
        print(f"airport-queue error: {e}")
        return jsonify({"error": str(e), "forecast": [], "queues": [], "flights": []})

def _maybe_write_airport_alert(data):
    """Write a single open SURGE/CRITICAL alert to aar_master_alerts (deduped)."""
    crit = [r for r in data.get("forecast", []) if r.get("status") in ("CRITICAL", "HIGH")]
    if not crit:
        return
    worst = max(crit, key=lambda r: r["gap"])
    try:
        conn = psycopg2.connect(os.getenv("HANUMIND_MEMORY_DB_URL"))
        cur = conn.cursor()
        # Dedup: at most one unresolved airport alert in any 6-hour window
        cur.execute("""SELECT 1 FROM aar_master_alerts
                       WHERE alert_type = 'Airport Queue Surge'
                       AND (resolved = false OR resolved IS NULL)
                       AND created_at > NOW() - INTERVAL '6 hours' LIMIT 1""")
        if cur.fetchone():
            cur.close(); conn.close(); return
        title = f"KLIA2 {worst['status']}: {worst['gap']} driver gap at {worst['clock']}"
        detail = (f"{worst['flights']} arrivals, {worst['pax']} pax, "
                  f"{worst['aar']} AAR bookings expected — {worst['needed']} drivers needed "
                  f"vs {worst['present']} present in queue.")
        cur.execute("""INSERT INTO aar_master_alerts
                       (alert_type, priority, title, detail, action_required, team,
                        acknowledged, resolved)
                       VALUES (%s,%s,%s,%s,%s,%s,false,false)""",
                    ('Airport Queue Surge', 'High', title, detail,
                     'Deploy drivers from PJ/Subang/Cheras with RM8/trip incentive',
                     'driverteam'))
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        print(f"airport alert write skipped: {e}")

@app.route("/api/fare-intelligence")
def api_fare_intelligence():
    return jsonify(read_all("Demand — Fare Intelligence"))

@app.route("/api/stats")
def api_stats():
    bookings = get_bookings()
    drivers = get_drivers()
    wati = get_wati_messages()
    flights = get_flights()
    total_bookings = len(bookings)
    on_track = len([b for b in bookings if b.get("Booking Status") in ["Confirmed","On The Way","Arrived","On Board"]])
    urgent = len([b for b in bookings if b.get("Escalation Status") == "Flagged"])
    completed = len([b for b in bookings if b.get("Booking Status") == "Completed"])
    cancelled = len([b for b in bookings if b.get("Booking Status") == "Cancelled"])
    compliant = len([d for d in drivers if d.get("Compliance Status") == "Active"])
    lapsing = len([d for d in drivers if d.get("Compliance Status") == "Lapsing"])
    lapsed = len([d for d in drivers if d.get("Compliance Status") == "Lapsed"])
    auto_resolved = len([m for m in wati if m.get("Resolution Status") == "Resolved"])
    escalated = len([m for m in wati if m.get("Resolution Status") == "Escalated"])
    expiry_warning = len([m for m in wati if float(str(m.get("Hours Until Expiry","99")).replace(",",".") or 99) < 2])
    surge_zones = len([f for f in flights if f.get("Zone Demand Level") == "Surge"])
    active_incentives = len([f for f in flights if f.get("Incentive Triggered") == "Yes"])
    return jsonify({
        "bookings": {"total": total_bookings, "on_track": on_track, "urgent": urgent, "completed": completed, "cancelled": cancelled},
        "drivers": {"total": len(drivers), "compliant": compliant, "lapsing": lapsing, "lapsed": lapsed},
        "wati": {"total": len(wati), "auto_resolved": auto_resolved, "escalated": escalated, "expiry_warning": expiry_warning},
        "flights": {"total": len(flights), "surge_zones": surge_zones, "active_incentives": active_incentives}
    })

@app.route("/api/master-alerts")
def api_master_alerts():
    team = request.args.get("team", None)
    show_resolved = request.args.get("show_resolved", "false") == "true"
    try:
        conn = psycopg2.connect(os.getenv("HANUMIND_MEMORY_DB_URL"))
        cur = conn.cursor()
        cols = "id, alert_type, priority, title, detail, action_required, acknowledged, created_at, team, acknowledged_by, acknowledged_at, resolved, resolved_by, resolved_at, resolution_note"
        order = "ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END"
        if show_resolved:
            where = "WHERE 1=1"
        else:
            where = "WHERE (resolved = false OR resolved IS NULL)"
        if team and team != "nerve_centre":
            cur.execute(f"SELECT {cols} FROM aar_master_alerts {where} AND team = %s {order}", (team,))
        else:
            cur.execute(f"SELECT {cols} FROM aar_master_alerts {where} {order}")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([{
            "id": r[0], "alert_type": r[1], "priority": r[2],
            "title": r[3], "detail": r[4], "action_required": r[5],
            "acknowledged": r[6], "created_at": str(r[7])[:16],
            "team": r[8], "acknowledged_by": r[9],
            "acknowledged_at": str(r[10])[:16] if r[10] else None,
            "resolved": r[11], "resolved_by": r[12],
            "resolved_at": str(r[13])[:16] if r[13] else None,
            "resolution_note": r[14]
        } for r in rows])
    except Exception as e:
        print(f"master-alerts error: {e}")
        return jsonify([])


@app.route("/api/master-alerts/<int:alert_id>/acknowledge", methods=["POST"])
def api_acknowledge_alert(alert_id):
    try:
        conn = psycopg2.connect(os.getenv("HANUMIND_MEMORY_DB_URL"))
        cur = conn.cursor()
        cur.execute("""
            UPDATE aar_master_alerts
            SET acknowledged = true, acknowledged_by = 'gowrish', acknowledged_at = NOW()
            WHERE id = %s
        """, (alert_id,))
        conn.commit()
        cur.close()
        conn.close()
    except:
        pass
    return jsonify({"status": "acknowledged"})

@app.route("/api/nerve-stats")
def api_nerve_stats():
    drivers = get_drivers()
    bookings = get_bookings()

    # Active Drivers — live from Drivers tab Compliance Status (1b)
    active_drivers = len([d for d in drivers if d.get("Compliance Status") == "Active"])

    def _num(v):
        try:
            return float(str(v).replace(",", "").strip() or 0)
        except Exception:
            return 0.0

    # Trips / GMV / fares — live from Bookings tab Booking Status + Booking Value (RM) (1a)
    completed = [b for b in bookings if b.get("Booking Status") == "Completed"]
    cancelled = [b for b in bookings if b.get("Booking Status") == "Cancelled"]
    noshow    = [b for b in bookings if b.get("Booking Status") == "No Show"]
    total_bookings = len(bookings)
    concluded = len(completed) + len(cancelled) + len(noshow)

    trips_today = len(completed)
    gmv_today = round(sum(_num(b.get("Booking Value (RM)")) for b in completed), 2)
    avg_fare = round(gmv_today / trips_today, 2) if trips_today else 0.0
    # Completion rate = completed of all concluded (completed + cancelled + no-show) trips.
    completion_rate = round(len(completed) / concluded * 100, 1) if concluded else 0.0
    # Cancellation rate = cancelled of all bookings today.
    cancellation_rate = round(len(cancelled) / total_bookings * 100, 1) if total_bookings else 0.0

    # NOTE: the Sheet holds only today's booking snapshot (no historical tab), so
    # weekly/monthly are projections of the Sheet-derived today figures, not history.
    weekly_trips  = trips_today * 7
    weekly_gmv    = round(gmv_today * 7, 2)
    monthly_trips = trips_today * 30
    monthly_gmv   = round(gmv_today * 30, 2)

    return jsonify({
        "trips_today": trips_today,
        "gmv_today": gmv_today,
        "completion_rate": completion_rate,
        "avg_fare": avg_fare,
        "cancellation_rate": cancellation_rate,
        "active_drivers": active_drivers,
        "weekly_gmv": weekly_gmv,
        "weekly_trips": weekly_trips,
        "monthly_gmv": monthly_gmv,
        "monthly_trips": monthly_trips
    })

@app.route("/api/companion/driver/<driver_id>")
def api_companion_driver(driver_id):
    try:
        drivers = get_drivers()
        idx = int(driver_id) - 1
        if 0 <= idx < len(drivers):
            d = drivers[idx]
            earnings = read_all("Driver — Earnings")
            earn = next((e for e in earnings if e.get("Driver ID") == d.get("Driver ID")), {})
            return jsonify({
                "name": d.get("Driver Name","Driver"),
                "zone": d.get("Zone","KLIA"),
                "compliance_status": d.get("Compliance Status","Active"),
                "rating": d.get("Rating", 4.5),
                "total_trips": d.get("Total Trips This Month", 0),
                "earnings_today": earn.get("Earnings RM", 150),
                "on_track": earn.get("On Track","Yes"),
                "weekly_target": earn.get("Weekly Target RM", 1000),
                "weekly_earned": earn.get("Weekly Earned So Far RM", 600),
                "tomorrow_zones": earn.get("Tomorrow Peak Zones","KLIA2, Petaling Jaya")
            })
    except:
        pass
    return jsonify({"name":"Ahmad bin Abdullah","zone":"KLIA2","compliance_status":"Active","rating":4.7,"total_trips":52,"earnings_today":185,"on_track":"Yes","weekly_target":1000,"weekly_earned":720,"tomorrow_zones":"KLIA2, Shah Alam"})

@app.route("/api/companion/ask", methods=["POST"])
def api_companion_ask():
    data = request.get_json()
    driver_id = int(data.get("driver_id", 1))
    question = data.get("question", "")
    if not question:
        return jsonify({"answer": "Please ask a question.", "source": "error"})
    result = ask(driver_id, question)
    return jsonify(result)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})



@app.route("/api/master-alerts/<int:alert_id>/resolve", methods=["POST"])
def api_resolve_alert(alert_id):
    data = request.get_json() or {}
    user = data.get("user", "Gowrish")
    note = data.get("note", "")
    if not note:
        return jsonify({"error": "Resolution note is required"}), 400
    try:
        conn = psycopg2.connect(os.getenv("HANUMIND_MEMORY_DB_URL"))
        cur = conn.cursor()
        cur.execute("""
            UPDATE aar_master_alerts
            SET resolved = true, resolved_by = %s, resolved_at = NOW(),
                resolution_note = %s, acknowledged = true,
                acknowledged_by = COALESCE(acknowledged_by, %s)
            WHERE id = %s
        """, (user, note, user, alert_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "resolved", "by": user})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
