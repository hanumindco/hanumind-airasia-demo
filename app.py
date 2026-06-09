import os
import psycopg2
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from sheets.sheets_client import (
    get_drivers, get_bookings, get_wati_messages,
    get_flights, get_compliance_summary, read_all
)
from agents.driver_companion import ask

load_dotenv('/Users/gowrishnambiar/hanumind_airasia_demo/.env')
app = Flask(__name__)

@app.route("/")
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

@app.route("/api/fare-intelligence")
def api_fare_intelligence():
    return jsonify(read_all("Fare Intelligence"))

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
    active_drivers = len([d for d in drivers if d.get("Compliance Status") == "Active"])

    # Realistic AirAsia Ride scale numbers
    trips_today = 1847
    avg_fare = 52.40
    gmv_today = round(trips_today * avg_fare, 2)
    completion_rate = 87.3
    cancellation_rate = 7.8
    weekly_trips = 12943
    weekly_gmv = round(weekly_trips * avg_fare, 2)
    monthly_trips = 55620
    monthly_gmv = round(monthly_trips * avg_fare, 2)

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
            earnings = read_all("Driver Earnings")
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
