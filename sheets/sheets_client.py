import os
import json
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import time

load_dotenv('/Users/gowrishnambiar/hanumind_airasia_demo/.env')

SHEET_ID = "1WQqDX4aWFF1Z86enfnkqaE2F9ZtfoaL9LPC84VOoB-g"
_client = None
_spreadsheet = None
_cache = {}
_cache_ttl = 120

def get_client():
    global _client, _spreadsheet
    if _client is None or _spreadsheet is None:
        creds_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'google_creds.json')
        if os.path.exists(creds_path):
            with open(creds_path) as f:
                creds_dict = json.load(f)
        else:
            creds_dict = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS"))
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        _client = gspread.authorize(creds)
        _spreadsheet = _client.open_by_key(SHEET_ID)
    return _spreadsheet

def get_sheet(tab_name):
    return get_client().worksheet(tab_name)

def read_all(tab_name):
    now = time.time()
    if tab_name in _cache and (now - _cache[tab_name]['ts']) < _cache_ttl:
        return _cache[tab_name]['data']
    data = get_sheet(tab_name).get_all_records()
    _cache[tab_name] = {'data': data, 'ts': now}
    return data

def read_rows(tab_name):
    return get_sheet(tab_name).get_all_values()

def update_row(tab_name, row_num, col_name, value):
    ws = get_sheet(tab_name)
    headers = ws.row_values(1)
    if col_name in headers:
        ws.update_cell(row_num, headers.index(col_name) + 1, value)

def get_drivers(): return read_all("Drivers")
def get_bookings(): return read_all("Bookings")
def get_wati_messages(): return read_all("WATI Messages")
def get_flights(): return read_all("Flights")
def get_compliance_summary(): return read_all("Driver — Compliance Summary")
def update_booking(row_num, col_name, value): update_row("Bookings", row_num, col_name, value)
def update_wati_message(row_num, col_name, value): update_row("WATI Messages", row_num, col_name, value)
def update_driver(row_num, col_name, value): update_row("Drivers", row_num, col_name, value)
def update_flight(row_num, col_name, value): update_row("Flights", row_num, col_name, value)
