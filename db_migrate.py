import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(os.getenv("HANUMIND_MEMORY_DB_URL"))
cur = conn.cursor()

tables = [
    """
    CREATE TABLE IF NOT EXISTS aar_drivers (
        id SERIAL PRIMARY KEY,
        driver_id TEXT UNIQUE,
        driver_name TEXT,
        phone_number TEXT,
        driver_type TEXT,
        zone TEXT,
        psv_licence_number TEXT,
        psv_expiry_date DATE,
        evp_number TEXT,
        evp_expiry_date DATE,
        insurance_provider TEXT,
        insurance_expiry_date DATE,
        puspakom_last_inspection DATE,
        puspakom_next_due DATE,
        compliance_status TEXT,
        reminder_sent TEXT,
        monthly_km INTEGER,
        budi95_tier TEXT,
        total_trips INTEGER,
        cancellation_count INTEGER,
        rating DECIMAL,
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_bookings (
        id SERIAL PRIMARY KEY,
        booking_id TEXT UNIQUE,
        source TEXT,
        customer_name TEXT,
        customer_phone TEXT,
        pickup_location TEXT,
        dropoff_location TEXT,
        pickup_date DATE,
        pickup_time TEXT,
        flight_number TEXT,
        number_of_pax INTEGER,
        special_requirements TEXT,
        assigned_driver_id TEXT,
        driver_name TEXT,
        booking_status TEXT,
        reminder_sent TEXT,
        driver_response TEXT,
        escalation_status TEXT,
        booking_value DECIMAL,
        cancellation_reason TEXT,
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_wati_messages (
        id SERIAL PRIMARY KEY,
        message_id TEXT UNIQUE,
        timestamp TIMESTAMP,
        sender_type TEXT,
        sender_name TEXT,
        sender_phone TEXT,
        message_content TEXT,
        classified_type TEXT,
        auto_response_sent TEXT,
        auto_response_content TEXT,
        escalated_to TEXT,
        resolution_status TEXT,
        chat_expiry_time TIMESTAMP,
        hours_until_expiry DECIMAL,
        expiry_warning_sent TEXT,
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_flights (
        id SERIAL PRIMARY KEY,
        flight_number TEXT,
        origin_city TEXT,
        origin_airport_code TEXT,
        scheduled_arrival_time TEXT,
        actual_arrival_time TEXT,
        delay_minutes INTEGER,
        passenger_count INTEGER,
        expected_ride_demand INTEGER,
        zone_demand_level TEXT,
        recommended_driver_count INTEGER,
        incentive_triggered TEXT,
        incentive_type TEXT,
        incentive_value DECIMAL,
        data_source TEXT,
        report_date DATE DEFAULT CURRENT_DATE,
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_compliance_summary (
        id SERIAL PRIMARY KEY,
        report_date DATE UNIQUE,
        total_active_drivers INTEGER,
        drivers_compliant INTEGER,
        drivers_lapsing INTEGER,
        drivers_lapsed INTEGER,
        reminders_sent_today INTEGER,
        jobs_blocked_today INTEGER,
        budi95_tier1 INTEGER,
        budi95_tier2 INTEGER,
        budi95_submission_status TEXT,
        apad_report_last_generated DATE,
        last_apad_access_date DATE,
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_driver_faq (
        id SERIAL PRIMARY KEY,
        question_keywords TEXT[],
        question_variations TEXT,
        answer TEXT,
        category TEXT,
        usage_count INTEGER DEFAULT 0,
        last_updated TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_response_cache (
        id SERIAL PRIMARY KEY,
        driver_id INTEGER,
        question_hash TEXT,
        question_text TEXT,
        answer_text TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        expires_at TIMESTAMP,
        served_count INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_driver_conversations (
        id SERIAL PRIMARY KEY,
        driver_id INTEGER,
        timestamp TIMESTAMP DEFAULT NOW(),
        message_type TEXT,
        content TEXT,
        source TEXT,
        tokens_used INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_driver_memory (
        id SERIAL PRIMARY KEY,
        driver_id INTEGER UNIQUE,
        memory_summary TEXT,
        memory_last_updated TIMESTAMP,
        total_conversations INTEGER DEFAULT 0,
        total_api_calls INTEGER DEFAULT 0,
        total_cache_hits INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_fare_intelligence (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT NOW(),
        zone TEXT,
        current_fare_multiplier DECIMAL,
        recommended_multiplier DECIMAL,
        traffic_condition TEXT,
        weather_condition TEXT,
        demand_level TEXT,
        competitor_grab_multiplier DECIMAL,
        competitor_indrive_note TEXT,
        flight_demand_contribution TEXT,
        event_demand_contribution TEXT,
        incentive_triggered BOOLEAN DEFAULT FALSE,
        incentive_type TEXT,
        incentive_value_rm DECIMAL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_zone_demand (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT NOW(),
        zone TEXT,
        drivers_present INTEGER,
        drivers_needed INTEGER,
        demand_level TEXT,
        demand_bar_percent INTEGER,
        status TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_master_alerts (
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT NOW(),
        alert_type TEXT,
        priority TEXT,
        title TEXT,
        detail TEXT,
        drivers_affected TEXT[],
        bookings_affected TEXT[],
        action_required TEXT,
        acknowledged BOOLEAN DEFAULT FALSE,
        acknowledged_by TEXT,
        acknowledged_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_driver_earnings (
        id SERIAL PRIMARY KEY,
        driver_id INTEGER,
        report_date DATE,
        shift_hours DECIMAL,
        trips_completed INTEGER,
        cancellations INTEGER,
        earnings_rm DECIMAL,
        top_zone TEXT,
        top_zone_earnings DECIMAL,
        weekly_target_rm DECIMAL,
        weekly_earned_so_far DECIMAL,
        on_track BOOLEAN,
        tomorrow_peak_zones TEXT,
        report_sent BOOLEAN DEFAULT FALSE,
        sent_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aar_dashboard_users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        last_login TIMESTAMP
    )
    """
]

print("Creating aar_ tables in hanumind_memory...")
for sql in tables:
    table_name = [line.strip() for line in sql.strip().split('\n') if 'CREATE TABLE' in line][0]
    cur.execute(sql)
    print(f"  OK: {table_name}")

conn.commit()
cur.close()
conn.close()
print("\nAll tables created successfully.")
