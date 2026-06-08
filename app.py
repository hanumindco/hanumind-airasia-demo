import os
import sys
import psycopg2
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from sheets.sheets_client import (
    get_drivers, get_bookings, get_wati_messages,
    get_flights, get_compliance_summary
)
from agents.driver_companion import ask

load_dotenv()
app = Flask(__name__)

# ── Main dashboard ────────────────────────────────────────────────────────────
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/companion")
def companion():
    return render_template("companion.html")

# ── Data APIs ─────────────────────────────────────────────────────────────────
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

# ── Companion APIs ────────────────────────────────────────────────────────────
@app.route("/api/companion/driver/<driver_id>")
def api_companion_driver(driver_id):
    try:
        drivers = get_drivers()
        idx = int(driver_id) - 1
        if 0 <= idx < len(drivers):
            d = drivers[idx]
            # also get earnings
            from sheets.sheets_client import read_all
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
    except Exception as e:
        pass
    return jsonify({
        "name":"Ahmad bin Abdullah","zone":"KLIA2","compliance_status":"Active",
        "rating":4.7,"total_trips":52,"earnings_today":185,
        "on_track":"Yes","weekly_target":1000,"weekly_earned":720,
        "tomorrow_zones":"KLIA2, Shah Alam"
    })

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
    return jsonify({"status": "ok", "agents": ["RELAY","TOWER","SPARK","PULSE","DRIVER_COMPANION"]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
