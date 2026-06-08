import gspread
from google.oauth2.service_account import Credentials
import json, os, random
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

CREDS_DICT = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS"))
SHEET_ID = os.getenv("GOOGLE_SHEETS_ID")
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(CREDS_DICT, scopes=scopes)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SHEET_ID)

random.seed(99)
today = datetime.today()

def fmt(d): return d.strftime("%Y-%m-%d")

# ── TAB 6 — DRIVER EARNINGS ───────────────────────────────────────────────────
print("Adding Driver Earnings tab...")
try:
    sh.add_worksheet(title="Driver Earnings", rows=110, cols=15)
except:
    pass
ws = sh.worksheet("Driver Earnings")
ws.clear()

MY_FIRST = ["Ahmad","Farid","Nurul","Siti","Rajesh","Priya","Wei","Mei","Hassan","Amirah",
            "Zulaikha","Hafiz","Kavitha","Suresh","Lim","Tan","Ismail","Rohani","Deepa","Muthu",
            "Azman","Norzahra","Ganesh","Chandran","Suraya","Faizal","Roslinda","Shankar","Aisha","Devi",
            "Mohd","Noraini","Vijay","Lakshmi","Azrin","Haslinda","Rajan","Suhana","Bala","Kamala",
            "Rizwan","Fatimah","Gopal","Meena","Azrul","Nabilah","Arjun","Selvi","Fadzil","Rubini"]
MY_LAST  = ["bin Abdullah","binti Yusof","a/l Kumar","a/p Devi","bin Hassan","binti Ahmad",
            "Lim","Tan","Wong","Ng","bin Razak","binti Ismail","a/l Muthu","bin Kassim",
            "binti Zainudin","bin Othman","binti Hamid","a/l Rajan","bin Mansor","binti Salleh"]
ZONES = ["KLIA","KLIA2","Petaling Jaya","Subang","Shah Alam","Cheras","Ampang","Klang"]

headers = ["Driver ID","Driver Name","Report Date","Shift Hours","Trips Completed",
           "Cancellations","Earnings RM","Top Zone","Top Zone Earnings RM",
           "Weekly Target RM","Weekly Earned So Far RM","On Track","Tomorrow Peak Zones","Report Sent"]
rows = [headers]
for i in range(1, 101):
    did = f"DRV{i:03d}"
    name = f"{random.choice(MY_FIRST)} {random.choice(MY_LAST)}"
    shift = round(random.uniform(4, 12), 1)
    trips = random.randint(8, 28)
    cancels = random.randint(0, 3)
    earnings = round(random.uniform(80, 320), 2)
    top_zone = random.choice(ZONES)
    top_zone_earn = round(earnings * random.uniform(0.4, 0.7), 2)
    weekly_target = random.choice([800, 900, 1000, 1100, 1200, 1400])
    days_in = random.randint(1, 5)
    weekly_earned = round(earnings * days_in * random.uniform(0.8, 1.1), 2)
    on_track = "Yes" if weekly_earned >= (weekly_target / 7 * days_in * 0.9) else "No"
    tomorrow_zones = ", ".join(random.sample(ZONES, 2))
    rows.append([did, name, fmt(today), shift, trips, cancels, earnings,
                 top_zone, top_zone_earn, weekly_target, weekly_earned,
                 on_track, tomorrow_zones, "No"])
ws.update(rows, value_input_option="RAW")
print(f"  Driver Earnings: {len(rows)-1} rows written")

# ── TAB 7 — FARE INTELLIGENCE ─────────────────────────────────────────────────
print("Adding Fare Intelligence tab...")
try:
    sh.add_worksheet(title="Fare Intelligence", rows=30, cols=12)
except:
    pass
ws2 = sh.worksheet("Fare Intelligence")
ws2.clear()

headers2 = ["Timestamp","Zone","Current Multiplier","Recommended Multiplier",
            "Traffic Condition","Weather Condition","Demand Level",
            "Grab Multiplier (simulated)","Incentive Triggered","Incentive Type","Incentive Value RM"]
rows2 = [headers2]
traffic_by_hour = {
    6:"Moderate", 7:"Heavy", 8:"Heavy", 9:"Moderate", 10:"Light", 11:"Light",
    12:"Moderate", 13:"Heavy", 14:"Heavy", 15:"Moderate", 16:"Moderate",
    17:"Heavy", 18:"Heavy", 19:"Heavy", 20:"Moderate", 21:"Gridlock",
    22:"Heavy", 23:"Moderate", 0:"Light", 1:"Light", 2:"Light", 3:"Light", 4:"Light", 5:"Light"
}
demand_by_hour = {
    6:"High", 7:"Surge", 8:"Surge", 9:"High", 10:"Medium", 11:"Medium",
    12:"High", 13:"High", 14:"Surge", 15:"High", 16:"Medium",
    17:"High", 18:"Surge", 19:"Surge", 20:"High", 21:"Surge",
    22:"High", 23:"Medium", 0:"Low", 1:"Low", 2:"Low", 3:"Low", 4:"Low", 5:"Medium"
}
multiplier_by_demand = {"Low":1.0, "Medium":1.2, "High":1.5, "Surge":2.0}

for hour in range(24):
    ts = today.replace(hour=hour, minute=0, second=0).strftime("%Y-%m-%d %H:%M")
    zone = random.choice(ZONES)
    traffic = traffic_by_hour[hour]
    demand = demand_by_hour[hour]
    current = multiplier_by_demand[demand]
    recommended = round(current * random.uniform(0.95, 1.15), 2)
    grab = round(current * random.uniform(1.0, 1.3), 2)
    weather = random.choice(["Clear","Clear","Cloudy","Rain"]) if hour in range(14,20) else "Clear"
    incentive = "Yes" if demand == "Surge" else "No"
    inc_type = random.choice(["Bonus per trip","Double points"]) if incentive == "Yes" else ""
    inc_value = random.choice([5, 8, 10]) if incentive == "Yes" else ""
    rows2.append([ts, zone, current, recommended, traffic, weather, demand,
                  grab, incentive, inc_type, inc_value])
ws2.update(rows2, value_input_option="RAW")
print(f"  Fare Intelligence: {len(rows2)-1} rows written")

# ── TAB 8 — MASTER ALERTS ────────────────────────────────────────────────────
print("Adding Master Alerts tab...")
try:
    sh.add_worksheet(title="Master Alerts", rows=15, cols=10)
except:
    pass
ws3 = sh.worksheet("Master Alerts")
ws3.clear()

headers3 = ["Alert ID","Created At","Priority","Title","Detail",
            "Drivers Affected","Bookings Affected","Action Required","Acknowledged"]
alerts = [
    ("ALT001", today.strftime("%Y-%m-%d %H:%M"), "High",
     "Ahmad Razif EVP expires in 8 days — active KLOOK booking on 12 Jun",
     "Driver DRV047 has EVP expiring 16 Jun. Confirmed KLOOK booking on 12 Jun. Risk of no driver if EVP lapses.",
     "DRV047", "BK0089", "Reassign BK0089 or confirm EVP renewal before 12 Jun.", "No"),
    ("ALT002", today.strftime("%Y-%m-%d %H:%M"), "High",
     "Shah Alam undersupply — 6 drivers needed, 2 present at 7PM peak",
     "Surge demand at 7PM. Only 2 drivers in Shah Alam. Gap of 4 drivers. Event at Stadium Shah Alam contributing.",
     "", "", "Activate incentive for Shah Alam. Reposition drivers from Subang and PJ.", "No"),
    ("ALT003", today.strftime("%Y-%m-%d %H:%M"), "Medium",
     "Cheras zone — 4 cancellations from DRV023 in 48 hours",
     "DRV023 Ganesh a/l Rajan has 4 cancellations in 48 hours. Cancellation rate 18% this week.",
     "DRV023", "", "Review cancellation reasons. Contact driver. Flag if pattern continues.", "No"),
    ("ALT004", today.strftime("%Y-%m-%d %H:%M"), "Plan",
     "Coldplay concert — Bukit Jalil — 14 Jun — 65,000 attendance",
     "Peak departure 10PM to 1AM. Recommend 40 additional drivers in Cheras, Ampang, city centre from 9PM.",
     "", "", "Pre-activate incentives from 8PM on 14 Jun. Brief Driver Team Lead by 12 Jun.", "No"),
]
rows3 = [headers3] + [list(a) for a in alerts]
ws3.update(rows3, value_input_option="RAW")
print(f"  Master Alerts: {len(rows3)-1} rows written")

print("\nAll 3 new tabs populated successfully.")
