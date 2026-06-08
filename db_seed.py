import psycopg2
import os
import bcrypt
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(os.getenv("HANUMIND_MEMORY_DB_URL"))
cur = conn.cursor()

# ── Login user ────────────────────────────────────────────────────────────────
print("Creating master login user...")
password = "airasia2026"
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
cur.execute("""
    INSERT INTO aar_dashboard_users (username, password_hash, role)
    VALUES (%s, %s, %s)
    ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash
""", ("gowrish", password_hash, "master"))
print("  Login: gowrish / airasia2026")

# ── FAQ entries ───────────────────────────────────────────────────────────────
print("Seeding FAQ table...")
faqs = [
    (["psv","renew","licence","lesen"], "How do I renew my PSV licence?",
     "To renew your PSV licence: 1) Visit any JPJ office or renew online at jpjebiz.jpj.gov.my. 2) Bring your current PSV licence, IC, and medical certificate from a registered clinic. 3) Pay the renewal fee (approximately RM 30). 4) Renewal takes 1 to 3 working days. Renew at least 30 days before expiry to avoid being blocked from jobs.", "PSV"),

    (["evp","renew","vehicle","permit"], "How do I renew my EVP?",
     "EVP renewal: 1) Log in to the APAD portal at apad.gov.my. 2) Submit your vehicle inspection report from PUSPAKOM. 3) Pay the EVP renewal fee. 4) Processing takes 3 to 5 working days. Your vehicle must pass PUSPAKOM inspection before EVP can be renewed.", "EVP"),

    (["puspakom","inspection","check","kereta"], "When do I need PUSPAKOM inspection?",
     "PUSPAKOM inspection is required every 6 months for e-hailing vehicles. Book online at puspakom.com.my or walk in to any PUSPAKOM centre. Cost is approximately RM 65. Bring your vehicle registration card and current EVP. Inspection takes about 45 minutes.", "EVP"),

    (["insurance","takaful","renew","insurans"], "How do I renew my vehicle insurance?",
     "Renew your e-hailing vehicle insurance through any general insurance provider — Allianz, Etiqa, Takaful Malaysia, AIG, or Zurich. Make sure you get commercial e-hailing coverage, not personal use only. Cost varies between RM 800 and RM 2,500 depending on vehicle type. Renew before expiry to avoid being blocked from jobs.", "Compliance"),

    (["budi95","petrol","subsidy","minyak"], "How does the BUDI95 fuel subsidy work?",
     "BUDI95 gives you subsidised RON95 petrol based on your monthly mileage. Tier 1 is below 2,000km per month — standard subsidy rate. Tier 2 is above 2,000km per month — higher subsidy rate. Your mileage is tracked automatically. Subsidy is credited to your MyKad at participating petrol stations.", "Earnings"),

    (["earning","pendapatan","how much","berapa"], "How much can I earn per day?",
     "Average earnings depend on your zone and hours. KLIA and KLIA2 zone drivers earn RM 150 to RM 320 per day on peak days. City zone drivers earn RM 80 to RM 200 per day. Peak hours are 6AM to 9AM, 12PM to 2PM, and 6PM to 10PM. Working all three peak windows gives you the highest daily earnings.", "Earnings"),

    (["peak","masa","time","bila"], "What are the peak hours?",
     "Peak hours for AirAsia Ride: Morning peak 6AM to 9AM — airport transfers and office commuters. Afternoon peak 12PM to 2PM — lunch and airport arrivals. Evening peak 6PM to 10PM — airport arrivals and after-work. Night surge after 10PM during weekends and events. Position yourself near KLIA2 or city centre before peak starts.", "Earnings"),

    (["cancel","cancellation","pembatalan","booking"], "Why was my booking cancelled?",
     "Bookings can be cancelled by the customer, B2B partner, or hospital. When a booking is cancelled you will receive a notification. Cancellations outside your control do not affect your rating. If you cancelled the booking yourself it counts toward your cancellation rate. Keep cancellations below 5% to maintain good standing.", "General"),

    (["rating","star","bintang","review"], "How is my driver rating calculated?",
     "Your rating is the average of all customer ratings over the past 90 days. Each ride is rated 1 to 5 stars. Ratings below 4.0 trigger a review. To improve your rating: arrive on time, keep the car clean, be polite, confirm the booking before departure. Ratings above 4.5 qualify you for priority job allocation.", "General"),

    (["incentive","bonus","reward","hadiah"], "How do incentives work?",
     "Incentives are triggered automatically during surge demand periods. When a zone shows High or Surge demand, you receive a bonus per trip completed in that zone. Bonus types: extra RM per trip, double points, or fixed payout. Check the driver app for active incentives in your zone. Incentives are credited to your account within 48 hours.", "Earnings"),

    (["zone","kawasan","area","mana"], "Which zone should I go to?",
     "Zone recommendation depends on time of day. Morning 6AM to 9AM: KLIA2 and city centre. Afternoon 2PM to 5PM: shopping centres — Mid Valley, Sunway, Pavilion. Evening 6PM to 10PM: KLIA2 and Bukit Bintang. Check the driver app for live zone demand before repositioning. High and Surge zones have active incentives.", "Earnings"),

    (["complaint","aduan","report","masalah"], "How do I report a problem with a customer?",
     "To report a customer issue: 1) Message AirAsia Ride support via WhatsApp immediately after the trip. 2) Describe the incident clearly — date, time, booking ID, and what happened. 3) Our team reviews within 24 hours. 4) For safety incidents call our emergency line immediately. Your report is treated confidentially.", "General"),

    (["payment","bayar","duit","transfer"], "When do I receive my earnings?",
     "Earnings are transferred to your registered bank account every Monday for the previous week's completed trips. Make sure your bank account details in the driver app are correct and up to date. If you have not received payment after 3 working days contact driver support with your driver ID.", "Earnings"),

    (["accident","accident","langgar","crash"], "What do I do if I have an accident?",
     "If you have an accident: 1) Ensure everyone is safe. Call 999 if anyone is injured. 2) Do not move vehicles until police arrive for serious accidents. 3) Take photos of all vehicles and damage. 4) Get the other driver's IC and vehicle plate. 5) File a police report within 24 hours. 6) Notify AirAsia Ride support immediately with your booking ID.", "General"),

    (["app","application","phone","telefon"], "The driver app is not working. What do I do?",
     "If the driver app is not working: 1) Force close the app and reopen. 2) Check your internet connection. 3) Clear the app cache in your phone settings. 4) If the problem continues log out and log back in. 5) If still not working uninstall and reinstall the app. 6) Contact driver support if the issue persists after reinstalling.", "General"),
]

for keywords, variations, answer, category in faqs:
    cur.execute("""
        INSERT INTO aar_driver_faq (question_keywords, question_variations, answer, category)
        VALUES (%s, %s, %s, %s)
    """, (keywords, variations, answer, category))

print(f"  {len(faqs)} FAQ entries seeded")

# ── Master alerts seed ────────────────────────────────────────────────────────
print("Seeding master alerts...")
alerts = [
    ("Compliance", "High", "Ahmad Razif EVP expires in 8 days — active KLOOK booking on 12 Jun",
     "Driver DRV047 Ahmad Razif bin Hassan has EVP expiring 16 Jun 2026. He has a confirmed KLOOK booking on 12 Jun. If EVP lapses before renewal he will be blocked and the booking will have no driver.",
     ["DRV047"], ["BK0089"], "Reassign BK0089 or confirm Ahmad Razif renews EVP before 12 Jun."),

    ("Supply", "High", "Shah Alam undersupply — 6 drivers needed, 2 present at 7PM peak",
     "Zone Shah Alam shows Surge demand at 7PM tonight based on flight arrivals and an event at Stadium Shah Alam. Only 2 drivers currently positioned. 6 drivers recommended. Gap of 4 drivers.",
     [], [], "Activate incentive for Shah Alam zone. Message available drivers in Subang and PJ to reposition."),

    ("Safety", "Medium", "Cheras zone — 4 cancellations from DRV023 in 48 hours",
     "Driver DRV023 Ganesh a/l Rajan has 4 cancellations in the past 48 hours. Pattern suggests either vehicle issue or selective job acceptance. Cancellation rate now at 18% this week.",
     ["DRV023"], [], "Review DRV023 cancellation reasons. Contact driver for explanation. Flag for review if pattern continues."),

    ("Event", "Plan", "Coldplay concert — Bukit Jalil — 14 Jun — 65,000 attendance",
     "Coldplay World Tour at Stadium Bukit Jalil on 14 Jun 2026. Estimated 65,000 attendees. Peak departure window 10PM to 1AM. Recommend activating 40 additional drivers in Cheras, Ampang, and city centre zones from 9PM.",
     [], [], "Pre-activate incentives for Bukit Jalil zone from 8PM on 14 Jun. Brief Driver Team Lead by 12 Jun."),
]

for alert_type, priority, title, detail, drivers, bookings, action in alerts:
    cur.execute("""
        INSERT INTO aar_master_alerts
        (alert_type, priority, title, detail, drivers_affected, bookings_affected, action_required)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (alert_type, priority, title, detail, drivers, bookings, action))

print(f"  {len(alerts)} master alerts seeded")

conn.commit()
cur.close()
conn.close()
print("\nSeed complete.")
print("Login credentials: gowrish / airasia2026")
