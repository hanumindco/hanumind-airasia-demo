# AirAsia Ride — Operations Intelligence Demo
## Build Log — June 2026
### Built by Gowrish Nambiar — HanuMind

---

## OVERVIEW

A live AI operations intelligence system built specifically for AirAsia Ride.
Initiated by Gowrish Nambiar as a demonstration of what an AI operations layer
can do for AirAsia Ride daily ops. Built independently and presented to
Suruban (Head of Operations) as a proof of capability.

Demo URL: https://hanumind-airasia-demo-production.up.railway.app
Mobile companion: https://hanumind-airasia-demo-production.up.railway.app/companion
GitHub: https://github.com/hanumindco/hanumind-airasia-demo
Built: June 2026
Build duration: 1 day

---

## TECH STACK

Backend: Python Flask
Database: PostgreSQL on Railway
AI Engine: Anthropic Claude Sonnet (claude-sonnet-4-5)
Data Feed: Google Sheets API v4
Email: Gmail API SMTP
Hosting: Railway
Frontend: HTML5, CSS3, Vanilla JavaScript
Web Scraping: BeautifulSoup4, Requests
Scheduling: APScheduler
Auth: bcrypt password hashing
Version Control: GitHub (hanumindco/hanumind-airasia-demo)

---

## INFRASTRUCTURE

Railway project: hanumind-airasia-demo
Railway URL: hanumind-airasia-demo-production.up.railway.app
Demo database: PostgreSQL at acela.proxy.rlwy.net:52013
Shared memory database: hanumind_memory at acela.proxy.rlwy.net:30782
Google Sheet ID: 1WQqDX4aWFF1Z86enfnkqaE2F9ZtfoaL9LPC84VOoB-g
Google service account: hanumind-sheets@hip-catalyst-498803-p4.iam.gserviceaccount.com
Gmail sender: hanumind.co@gmail.com
Email recipient (demo): gowrish.exec@gmail.com

---

## DATABASE ARCHITECTURE

All tables use aar_ prefix inside hanumind_memory PostgreSQL.
Fully isolated from all other HanuMind client data.
No data from HanuMind master, Hima client, or Mirror appears in any aar_ table.

aar_drivers (100 rows) — Driver profiles, compliance dates, ratings, mileage
aar_bookings (150 rows) — All bookings: on demand, advance, B2B, hospital
aar_wati_messages (20 rows) — Incoming customer and driver WhatsApp messages
aar_flights (25 rows) — KLIA2 flight arrivals with demand calculations
aar_compliance_summary (7 rows) — Daily compliance snapshot for past 7 days
aar_driver_faq (15 rows) — Pre-loaded FAQ knowledge base for Driver Companion
aar_response_cache (dynamic) — 24-hour cache of Claude API responses
aar_driver_conversations (dynamic) — Full conversation log per driver
aar_driver_memory (dynamic) — Nightly driver memory summaries
aar_fare_intelligence (24 rows) — Hourly fare multiplier and traffic data
aar_zone_demand (dynamic) — Zone-level demand tracking per time slot
aar_master_alerts (4 rows) — Cross-system intelligence alerts
aar_driver_earnings (100 rows) — Daily earnings per driver with weekly targets
aar_dashboard_users (1 row) — Demo login credentials

---

## GOOGLE SHEETS — 8 TABS

Tab 1: Drivers (100 rows)
Columns: Driver ID, Driver Name, Phone Number, Driver Type, Zone,
PSV Licence Number, PSV Expiry Date, EVP Number, EVP Expiry Date,
Insurance Provider, Insurance Expiry Date, PUSPAKOM Last Inspection Date,
PUSPAKOM Next Due Date, Compliance Status, Reminder Sent, Monthly KM,
BUDI95 Tier, Total Trips This Month, Cancellation Count This Month, Rating

Tab 2: Bookings (150 rows)
Columns: Booking ID, Source, Customer Name, Customer Phone, Pickup Location,
Dropoff Location, Pickup Date, Pickup Time, Flight Number, Number of Pax,
Special Requirements, Assigned Driver ID, Driver Name, Booking Status,
Reminder Sent, Driver Response, Escalation Status, Booking Value RM, Cancellation Reason

Tab 3: WATI Messages (20 rows)
Columns: Message ID, Timestamp, Sender Type, Sender Name, Sender Phone,
Message Content, Classified Type, Auto Response Sent, Auto Response Content,
Escalated To, Resolution Status, Chat Expiry Time, Hours Until Expiry, Expiry Warning Sent

Tab 4: Flights (25 rows)
Columns: Flight Number, Origin City, Origin Airport Code, Scheduled Arrival Time,
Actual Arrival Time, Delay minutes, Passenger Count, Expected Ride Demand,
Zone Demand Level, Recommended Driver Count, Incentive Triggered,
Incentive Type, Incentive Value RM, Data Source

Tab 5: Compliance Summary (7 rows)
Columns: Report Date, Total Active Drivers, Drivers Compliant, Drivers Lapsing,
Drivers Lapsed, Reminders Sent Today, Jobs Blocked Today, BUDI95 Drivers Tier 1,
BUDI95 Drivers Tier 2, BUDI95 Submission Status, APAD Report Last Generated,
Last APAD Access Date

Tab 6: Driver Earnings (100 rows)
Columns: Driver ID, Driver Name, Report Date, Shift Hours, Trips Completed,
Cancellations, Earnings RM, Top Zone, Top Zone Earnings RM, Weekly Target RM,
Weekly Earned So Far RM, On Track, Tomorrow Peak Zones, Report Sent

Tab 7: Fare Intelligence (24 rows)
Columns: Timestamp, Zone, Current Multiplier, Recommended Multiplier,
Traffic Condition, Weather Condition, Demand Level, Grab Multiplier simulated,
Incentive Triggered, Incentive Type, Incentive Value RM

Tab 8: Master Alerts (4 rows)
Columns: Alert ID, Created At, Priority, Title, Detail,
Drivers Affected, Bookings Affected, Action Required, Acknowledged

---

## FILE STRUCTURE

hanumind_airasia_demo/
  app.py                          Flask app — all routes and API endpoints
  scheduler.py                    APScheduler job definitions
  requirements.txt                Python dependencies
  Procfile                        Railway start command
  railway.toml                    Railway build configuration
  BUILD_LOG.md                    This document
  db_migrate.py                   Creates all aar_ tables in hanumind_memory
  db_seed.py                      Seeds login, FAQ entries, master alerts
  populate_sheets.py              Populates all 5 original Google Sheet tabs
  populate_new_tabs.py            Populates Driver Earnings, Fare Intelligence, Master Alerts tabs

  agents/
    __init__.py
    relay.py                      WATI message classification and auto-response
    tower.py                      Booking operations and driver reminders
    spark.py                      Supply intelligence and demand forecasting
    pulse.py                      Regulatory compliance monitoring
    driver_companion.py           Three-layer Driver AI Companion

  scrapers/
    malaysia_airports_scraper.py  Scrapes KLIA2 live arrivals from Malaysia Airports
    events_scraper.py             Scrapes Klang Valley events from Ticket2u and Eventbrite

  sheets/
    __init__.py
    sheets_client.py              Google Sheets read/write client for all 8 tabs

  templates/
    dashboard.html                Main operations dashboard with two-tab layout
    companion.html                Mobile Driver AI Companion fullscreen

  static/
    style.css                     Shared styles

---

## ENVIRONMENT VARIABLES

ANTHROPIC_API_KEY — Claude API access
GOOGLE_SHEETS_ID — Google Sheet identifier
GOOGLE_SHEETS_CREDENTIALS — Service account JSON as single-line string
AIRASIA_DEMO_DB_URL — Demo PostgreSQL connection string
HANUMIND_MEMORY_DB_URL — Shared memory PostgreSQL connection string
GMAIL_USER — Sender email address
GMAIL_APP_PASSWORD — Gmail app password for SMTP
DRIVER_TEAM_LEAD_EMAIL — Morning brief recipient
PORT — Flask server port set by Railway

---

## AGENTS

RELAY — Customer and Driver Communications
File: agents/relay.py
Schedule: every 15 minutes
Production trigger: WATI webhook POST to /relay/webhook

What it does:
Reads all unresolved messages from WATI Messages Google Sheet.
Classifies each message into one of 5 types using Claude:
1. Driver Status Check: queries Bookings sheet, auto-replies with driver name and ETA
2. Refund Request: verifies booking, auto-approves clear cases, escalates disputed ones
3. Reschedule Request: acknowledges, logs, routes to control tower queue
4. Driver Complaint: acknowledges, logs against driver ID, routes to Driver Support
5. General Enquiry: responds from knowledge base
Monitors 24-hour WATI conversation expiry window.
Sends update to customer when under 2 hours remaining to prevent chat expiry cost.
Writes all classifications, responses, and escalations back to sheet in real time.

Production path:
Replace Google Sheet feed with live WATI webhook.
Zero code rebuild. One environment variable change: WATI_WEBHOOK_URL.
WATI supports webhooks via dashboard: More, Webhooks, Add webhook URL,
enable message received event.

---

TOWER — Booking Operations
File: agents/tower.py
Schedule: every 10 minutes

What it does:
Reads all bookings from Bookings Google Sheet.
Processes B2B intake from KLOOK, KKdays, KPJ, Sunway Medical, Hospital Form.
Logs automated driver reminder at 45 minutes before each pickup.
Flags booking as URGENT (red) if driver does not respond within 10 minutes.
Detects cancellations from any source and immediately updates dashboard.
Colour codes all bookings:
  Green: confirmed and on track
  Yellow: reminder sent, awaiting driver confirmation
  Red: urgent, driver not responding
  Orange: cancellation received, control tower notified
  Grey: completed or cancelled

Problem it solves:
Previously when hospitals or B2B partners cancelled bookings in the portal,
control tower had no visibility. Drivers called asking why their job disappeared
with no answer available. TOWER surfaces every cancellation with source and
reason within seconds.

Production path:
Replace Google Sheet with live booking portal API or webhook.
Hospital intake form at /intake — submissions POST directly to Flask.

---

SPARK — Supply Intelligence and Event Management
File: agents/spark.py
Schedule: data refresh every 30 minutes, morning brief daily at 6AM,
          event scan every Sunday at 8AM

What it does:
Scrapes KLIA2 arrivals from airports.malaysiaairports.com.my every 30 minutes.
For each flight: calculates expected ride demand based on passenger count,
time of day, and delay status.
Maps demand to 8 Klang Valley zones:
KLIA, KLIA2, Petaling Jaya, Subang, Shah Alam, Cheras, Ampang, Klang.
Generates driver positioning recommendation per zone per time slot.
Triggers incentive recommendation when demand hits Surge threshold.
Monitors upcoming events: concerts, football matches, F1, public holidays.
Sends morning brief email at 6AM to Driver Team Lead containing:
  peak demand windows, top flights by passenger count, zone demand map,
  active incentives, upcoming events, recommended driver count per shift.

Production path:
Upgrade scraper to FlightAware API (USD 50-200/month) or AirAsia Group internal data.
Incentive recommendations connect to AAR internal driver app API.
Intelligence layer fully built. API connection is the final step after hiring.

---

PULSE — Regulatory Compliance
File: agents/pulse.py
Schedule: every 60 minutes, BUDI95 report on 1st of each month at 9AM

What it does:
Checks PSV Licence, EVP, Insurance, and PUSPAKOM expiry for all 100 drivers.
Updates compliance status:
  Active: all documents valid beyond 30 days
  Lapsing: any document expires within 30 days
  Lapsed: any document already expired
Sends automated 30-day advance reminder to lapsing drivers with exact renewal steps.
Flags lapsed drivers as BLOCKED on dashboard immediately.
Calculates BUDI95 fuel subsidy tier per driver:
  Tier 1 below 2000km per month, Tier 2 above 2000km per month.
Generates BUDI95 submission report on 1st of each month at 9AM.
APAD compliance report generated on demand via dashboard button.

---

DRIVER AI COMPANION — Three-Layer Response System
File: agents/driver_companion.py
Endpoint: POST /api/companion/ask
Demo URL: /companion
Production: embed as WebView in AirAsia Ride driver app

Layer 1 — FAQ Cache (zero API cost)
Keyword match against 15 pre-loaded FAQ entries in aar_driver_faq.
Topics covered: PSV renewal, EVP renewal, PUSPAKOM, insurance, BUDI95,
earnings, peak hours, cancellations, ratings, incentives, zones,
complaints, payments, accidents, app troubleshooting.
Usage count tracked per FAQ entry. Instant response with no API call.

Layer 2 — Response Cache (zero API cost)
MD5 hash of question text matched against aar_response_cache.
24-hour TTL — expires and refreshes daily.
If 100 drivers ask the same question today, Claude is called once.
Served count tracked per cache entry.

Layer 3 — Personalised Claude API call
Fires only when Layer 1 and Layer 2 return no match.
Driver context injected into system prompt:
  name, zone, compliance status, rating, monthly KM, BUDI95 tier,
  today earnings, weekly target, weekly earned so far, on-track status,
  tomorrow peak zones, conversation history summary.
Language detection: auto-detects Bahasa Malaysia vs English.
Responds in the language the driver used.
Response saved to aar_response_cache for 24 hours.
All interactions logged to aar_driver_conversations with token count.

UI features:
Female futuristic pilot mascot (custom SVG, no external image dependencies)
AirAsia red header with driver name, avatar initial, EN/BM language toggle
Stats bar: today earnings, weekly track status, rating, trips, compliance status
Chat bubbles with source badge (FAQ, Cached, AI) controlled by DEMO_MODE flag
Quick reply buttons for 5 common questions in both English and Bahasa Malaysia
Typing indicator with animated dots while Claude response loads
Auto-resize textarea input
Mobile-first design with safe area padding for iPhone notch

Production embedding steps:
1. Set DEMO_MODE = false in companion.html — removes source badges from chat
2. Pass driver_id from app session via URL: /companion?driver=DRIVER_ID
3. Embed /companion as WebView in the AirAsia Ride driver app
4. Zero rebuild required

---

## API ENDPOINTS

GET  /                        Main operations dashboard
GET  /companion               Fullscreen mobile Driver AI Companion
GET  /api/drivers             All 100 drivers from Google Sheet
GET  /api/bookings            All 150 bookings from Google Sheet
GET  /api/wati                All 20 WATI messages from Google Sheet
GET  /api/flights             All 25 flights from Google Sheet
GET  /api/compliance          7-day compliance summary
GET  /api/stats               Aggregated stats for all dashboard counters
GET  /api/companion/driver/id Driver profile and earnings for Companion header
POST /api/companion/ask       Submit question to Driver AI Companion
GET  /health                  System health check

---

## DEMO DATA

All data is fictional but mirrors AirAsia Ride actual operational structure.

Drivers: 100 drivers across 8 Klang Valley zones.
Compliance mix: 60 Active, 30 Lapsing (within 30 days), 10 Lapsed.
BUDI95 mix: approximately 38 Tier 1 (below 2000km), 62 Tier 2 (above 2000km).
Ratings range: 3.8 to 5.0.

Bookings: 150 total.
50 On Demand, 50 Advance Booking.
10 KLOOK, 10 KKdays, 10 KPJ, 10 Sunway Medical, 10 Hospital Form.
5 bookings with no driver assigned.
5 hospital and B2B cancellations with Control Tower Notified escalation status.
8 bookings with no reminder sent yet.

WATI Messages: 20 total across 5 types.
6 Driver Status Check, 4 Refund Request, 3 Reschedule Request,
4 Driver Complaint, 3 General Enquiry.
3 messages approaching 24-hour expiry (shown in flashing red).

Flights: 25 KLIA2 arrivals across one day.
Peaks at 7AM (5 flights), 2PM (5 flights), 9PM (5 flights).
10 off-peak flights spread across the day.
Routes: Bangkok, Singapore, Jakarta, Bali, Manila,
Ho Chi Minh City, Colombo, Chennai, Mumbai.
18 on-time, 7 delayed.

Driver Earnings: 100 rows, one per driver.
Daily earnings RM 80 to RM 320.
Weekly targets RM 800 to RM 1400.
Mix of on-track and behind drivers.

Fare Intelligence: 24 rows (one per hour).
Multipliers rise during peak windows: 7AM, 2PM, 9PM.
Range: 1.0x (off-peak) to 2.0x (surge).
Grab comparison multiplier included for competitive context.

Master Alerts: 4 seeded alerts.
1. Ahmad Razif EVP expires in 8 days with active KLOOK booking conflict (High priority)
2. Shah Alam undersupply: 6 drivers needed, 2 present at 7PM peak (High priority)
3. Cheras zone: 4 cancellations from DRV023 in 48 hours (Medium priority)
4. Coldplay concert Bukit Jalil 14 Jun, 65000 attendance (Plan priority)

---

## DEMO LOGIN

URL: https://hanumind-airasia-demo-production.up.railway.app
Username: gowrish
Password: airasia2026

---

## PRODUCTION CHECKLIST — WHAT CHANGES WHEN HIRED

WATI messages
  Demo: Google Sheet simulation
  Production: Live WATI webhook to /relay/webhook

Flight data
  Demo: Malaysia Airports public page scraper
  Production: FlightAware API or AirAsia Group internal flight data

Hospital bookings
  Demo: Google Sheet form simulation
  Production: Live hospital intake form POSTing to Flask /intake

B2B bookings
  Demo: Google Sheet simulation
  Production: AAR booking portal API or webhook

Driver incentives
  Demo: Dashboard recommendation only
  Production: Push directly to driver app via AAR internal API

Driver Companion
  Demo: Standalone /companion URL with DEMO_MODE = true
  Production: Embedded WebView in AAR driver app, DEMO_MODE = false

Email recipients
  Demo: gowrish.exec@gmail.com
  Production: Driver Team Lead and ops manager email addresses

Driver and booking data
  Demo: Google Sheets with 100 and 150 fictional rows
  Production: AAR live database connected via API

---

## MONTHLY RUNNING COST

Anthropic API (Claude): RM 50 to RM 150 per month
Railway hosting: RM 20 to RM 45 per month
Google Sheets API: Free
Gmail API: Free
Malaysia Airports scraper: Free (public page)
OpenWeatherMap (future Fare Intelligence): Free tier sufficient
Total: RM 70 to RM 195 per month

If upgraded to FlightAware commercial API: add USD 50 to USD 200 per month.

---

## BUILD TIMELINE

8 Jun 2026 — Google Sheet created with 5 tabs, service account configured
8 Jun 2026 — Project folder structure created, all empty files scaffolded
8 Jun 2026 — requirements.txt, .env, Procfile, railway.toml configured
8 Jun 2026 — sheets_client.py built and tested, all 5 tabs reading correctly
8 Jun 2026 — app.py built with all API endpoints
8 Jun 2026 — dashboard.html built with RELAY, TOWER, SPARK, PULSE sections
8 Jun 2026 — Dashboard confirmed live locally on port 5001
8 Jun 2026 — GitHub repo created: hanumindco/hanumind-airasia-demo
8 Jun 2026 — Deployed to Railway: hanumind-airasia-demo-production.up.railway.app
8 Jun 2026 — 14 aar_ tables created in hanumind_memory PostgreSQL
8 Jun 2026 — Login user seeded (gowrish / airasia2026)
8 Jun 2026 — 15 FAQ entries seeded into aar_driver_faq
8 Jun 2026 — 4 master alerts seeded into aar_master_alerts
8 Jun 2026 — 3 new Google Sheet tabs added: Driver Earnings, Fare Intelligence, Master Alerts
8 Jun 2026 — Driver AI Companion built: three-layer system, mobile UI, female pilot mascot SVG
8 Jun 2026 — Two-tab dashboard: Operations and Driver AI Companion with phone frame mockup
8 Jun 2026 — 11 LEARN entries written to hanumind_memory agent_learnings table
8 Jun 2026 — BUILD_LOG.md created

---

## CONTACT

Built by: Gowrish Nambiar
Email: hanumind.co@gmail.com
Location: Johor Bahru, Malaysia
Product: HanuMind — Personal AI Operating System

This document is a living log. Updated after every build session.
