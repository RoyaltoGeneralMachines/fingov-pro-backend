# db.py
# Central DB management for Fingov Pro Cloud Server
import sqlite3
import os

DB_PATH = os.environ.get("FINGOV_DB_PATH", "fingov_cloud.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # ---- USERS TABLE ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        full_name TEXT,
        device_id TEXT,
        created_at TEXT
    );
    """)

    # ---- OTP TABLE ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS otp_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        otp TEXT,
        expiry TEXT,
        created_at TEXT
    );
    """)

    # ---- GENERIC TEMPLATE STORAGE ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS generic_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        template TEXT,
        version TEXT,
        updated_by TEXT,
        updated_at TEXT
    );
    """)

    # ---- PARTNERS TABLE ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS partners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partner_code TEXT,
        partner_name TEXT,
        login_id TEXT,
        mobile TEXT,
        created_at TEXT,
        updated_at TEXT
    );
    """)

    # ---- SYNC LEDGER ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sync_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT,
        remote_id TEXT,
        data TEXT,
        created_at TEXT
    );
    """)

    # ---- D2NA ARMY LOGS ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS d2na_army_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        agent_code TEXT,
        agent_name TEXT,
        service_type TEXT,
        customer_name TEXT,
        account_or_ack_no TEXT,
        file_sent_path TEXT,
        notes TEXT,
        handled_by TEXT,
        device_id TEXT,
        created_at TEXT,
        remote_id TEXT,
        synced INTEGER DEFAULT 0
    );
    """)

    # ---- PAN RECORDS ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pan_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_no TEXT,
        name TEXT,
        ack TEXT,
        password TEXT,
        date TEXT,
        whatsapp TEXT,
        pan_type TEXT,
        mode TEXT,
        pan_number TEXT,
        note TEXT,
        allotment_date TEXT,
        file_path TEXT,
        agent_code TEXT,
        agent_name TEXT,
        include_agent INTEGER,
        device_id TEXT,
        created_at TEXT,
        synced INTEGER DEFAULT 0,
        remote_id TEXT
    );
    """)

    # ---- KOTAK RECORDS ----
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kotak_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_no TEXT,
        name TEXT,
        date TEXT,
        shop TEXT,
        account TEXT,
        crn TEXT,
        ifsc TEXT,
        whatsapp TEXT,
        note TEXT,
        agent_code TEXT,
        agent_name TEXT,
        include_agent INTEGER,
        global_image_path TEXT,
        device_id TEXT,
        created_at TEXT,
        synced INTEGER DEFAULT 0,
        remote_id TEXT
    );
    """)

    # ⭐⭐⭐ NEW: WHATSAPP SEND LOGS ⭐⭐⭐
    cur.execute("""
    CREATE TABLE IF NOT EXISTS wa_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        to_number TEXT,
        message TEXT,
        file_path TEXT,
        template_key TEXT,
        sent_by TEXT,
        sent_by_role TEXT,
        device_id TEXT,
        created_at TEXT,
        result TEXT
    );
    """)

    conn.commit()
    conn.close()
