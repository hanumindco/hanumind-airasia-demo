import os
import hashlib
import psycopg2
from datetime import datetime, timedelta
from anthropic import Anthropic
from dotenv import load_dotenv
load_dotenv()

client = Anthropic()

def get_db():
    return psycopg2.connect(os.getenv("HANUMIND_MEMORY_DB_URL"))

def detect_language(text):
    malay_words = ["saya","awak","boleh","nak","macam","mana","bila","kenapa",
                   "berapa","tolong","terima","kasih","encik","puan","lesen",
                   "kenderaan","pendapatan","semak","renew","tamat","adakah","minggu"]
    text_lower = text.lower()
    hits = sum(1 for w in malay_words if w in text_lower)
    return "ms" if hits >= 2 else "en"

def get_driver_memory(conn, driver_id):
    cur = conn.cursor()
    cur.execute("SELECT memory_summary FROM aar_driver_memory WHERE driver_id = %s", (driver_id,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None

def log_conversation(conn, driver_id, message_type, content, source, tokens=0):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO aar_driver_conversations
        (driver_id, message_type, content, source, tokens_used)
        VALUES (%s, %s, %s, %s, %s)
    """, (driver_id, message_type, content, source, tokens))
    conn.commit()
    cur.close()

def layer1_faq(conn, question, language):
    cur = conn.cursor()
    cur.execute("SELECT id, answer, question_keywords FROM aar_driver_faq")
    faqs = cur.fetchall()
    cur.close()
    q_lower = question.lower()
    for faq_id, answer, keywords in faqs:
        if keywords and any(kw.lower() in q_lower for kw in keywords):
            cur2 = conn.cursor()
            cur2.execute("UPDATE aar_driver_faq SET usage_count = usage_count + 1 WHERE id = %s", (faq_id,))
            conn.commit()
            cur2.close()
            return answer
    return None

def layer2_cache(conn, driver_id, question):
    q_hash = hashlib.md5(question.lower().strip().encode()).hexdigest()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, answer_text FROM aar_response_cache
        WHERE driver_id = %s AND question_hash = %s AND expires_at > NOW()
        ORDER BY created_at DESC LIMIT 1
    """, (driver_id, q_hash))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE aar_response_cache SET served_count = served_count + 1 WHERE id = %s", (row[0],))
        conn.commit()
    cur.close()
    return row[1] if row else None

def save_to_cache(conn, driver_id, question, answer):
    q_hash = hashlib.md5(question.lower().strip().encode()).hexdigest()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO aar_response_cache
        (driver_id, question_hash, question_text, answer_text, expires_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (driver_id, q_hash, question, answer, datetime.now() + timedelta(hours=24)))
    conn.commit()
    cur.close()

def layer3_api(conn, driver_id, question, language):
    from sheets.sheets_client import get_drivers, read_all
    drivers = get_drivers()
    earnings = read_all("Driver Earnings")
    driver_info = drivers[driver_id-1] if driver_id <= len(drivers) else {}
    earn_info = next((e for e in earnings if e.get("Driver ID") == driver_info.get("Driver ID","")), {})
    memory = get_driver_memory(conn, driver_id)

    context = f"""
Driver: {driver_info.get('Driver Name','Unknown')}
Zone: {driver_info.get('Zone','Unknown')}
Compliance: {driver_info.get('Compliance Status','Unknown')}
Rating: {driver_info.get('Rating',0)}
Trips this month: {driver_info.get('Total Trips This Month',0)}
Today earnings: RM {earn_info.get('Earnings RM',0)}
Weekly target: RM {earn_info.get('Weekly Target RM',1000)}
Weekly earned so far: RM {earn_info.get('Weekly Earned So Far RM',0)}
On track: {earn_info.get('On Track','Unknown')}
Tomorrow peak zones: {earn_info.get('Tomorrow Peak Zones','KLIA2, Petaling Jaya')}
BUDI95 tier: {driver_info.get('BUDI95 Tier','Tier 1')}
Monthly KM: {driver_info.get('Monthly KM',0)}
"""
    if memory:
        context += f"\nHistory: {memory}"

    lang_instruction = "Respond in Bahasa Malaysia. Be warm and encouraging." if language == "ms" else "Respond in English. Be warm and encouraging."

    system = f"""You are an AI assistant for AirAsia Ride drivers in Malaysia.
Help drivers with earnings, compliance, zones, and operations.
Use plain text only. No asterisks, no markdown symbols, no em dashes, no bullet points, no hyphens as bullets. Use numbers for lists like 1) 2) 3). Use line breaks between points. Be concise, specific, and personal — use the driver's actual data in your response.
Never give generic answers when you have real data available.
{lang_instruction}

Driver context:
{context}"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        system=system,
        messages=[{"role":"user","content":question}]
    )
    answer = response.content[0].text
    tokens = response.usage.input_tokens + response.usage.output_tokens
    save_to_cache(conn, driver_id, question, answer)
    return answer, tokens

def ask(driver_id, question):
    conn = get_db()
    language = detect_language(question)
    log_conversation(conn, driver_id, "question", question, "user", 0)

    answer = layer1_faq(conn, question, language)
    if answer:
        log_conversation(conn, driver_id, "answer", answer, "faq_cache", 0)
        conn.close()
        return {"answer": answer, "source": "faq_cache", "language": language}

    answer = layer2_cache(conn, driver_id, question)
    if answer:
        log_conversation(conn, driver_id, "answer", answer, "response_cache", 0)
        conn.close()
        return {"answer": answer, "source": "response_cache", "language": language}

    answer, tokens = layer3_api(conn, driver_id, question, language)
    log_conversation(conn, driver_id, "answer", answer, "api_call", tokens)
    conn.close()
    return {"answer": answer, "source": "api_call", "language": language, "tokens": tokens}
