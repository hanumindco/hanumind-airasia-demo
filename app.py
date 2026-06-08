import os
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
from sheets.sheets_client import (
    get_drivers, get_bookings, get_wati_messages,
    get_flights, get_compliance_summary
)

load_dotenv()

app = Flask(__name__)

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

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
    expiry_warning = len([m for m in wati if str(m.get("Hours Until Expiry","99")) and float(str(m.get("Hours Until Expiry","99")).replace(",",".") or 99) < 2])

    surge_zones = len([f for f in flights if f.get("Zone Demand Level") == "Surge"])
    active_incentives = len([f for f in flights if f.get("Incentive Triggered") == "Yes"])

    return jsonify({
        "bookings": {
            "total": total_bookings,
            "on_track": on_track,
            "urgent": urgent,
            "completed": completed,
            "cancelled": cancelled
        },
        "drivers": {
            "total": len(drivers),
            "compliant": compliant,
            "lapsing": lapsing,
            "lapsed": lapsed
        },
        "wati": {
            "total": len(wati),
            "auto_resolved": auto_resolved,
            "escalated": escalated,
            "expiry_warning": expiry_warning
        },
        "flights": {
            "total": len(flights),
            "surge_zones": surge_zones,
            "active_incentives": active_incentives
        }
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok", "agents": ["RELAY","TOWER","SPARK","PULSE"]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
