# db.py
# Central DB management for Fingov Pro Cloud Server

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool


# -------------------------
# DATABASE CONFIG
# -------------------------

# Default Render PostgreSQL connection (auto-connect if env var not set)
DEFAULT_RENDER_DB = (
    "postgresql://fingov_pro_db_user:"
    "8331F1E5oXSItkRrJbFFmlJ5vR144iwl"
    "@dpg-d4hdudili9vc73e562g0-a.oregon-postgres.render.com/"
    "fingov_pro_db"
)

DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_RENDER_DB)

# SQLAlchemy Engine (for ORM or pooled access)
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"connect_timeout": 10},
    echo=False
)


# -------------------------
# CONNECTION HANDLER
# -------------------------
def get_conn():
    """
    Establish a PostgreSQL database connection.
    Connects to Render's PostgreSQL using DATABASE_URL,
    with automatic fallback to local PostgreSQL if Render connection fails.
    """

    db_url = DATABASE_URL

    # Validate URL
    result = urlparse(db_url)
    if not all([result.scheme, result.hostname, result.path]):
        raise RuntimeError("Invalid DATABASE_URL. Check your Render connection string.")

    try:
        # Primary Render connection
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        return conn

    except Exception as e:
        # Local fallback (developer use)
        try:
            return psycopg2.connect(
                host="localhost",
                dbname="fingov_local",
                user="postgres",
                password="postgres",
                cursor_factory=RealDictCursor,
            )
        except Exception as fallback_error:
            raise RuntimeError(
                f"Database connection failed. Primary: {e}, Fallback: {fallback_error}"
            )


# -------------------------
# INITIALIZE DATABASE STRUCTURE
# -------------------------
def init_db():
    """
    Initializes all required tables if they don't exist.
    Safe to run multiple times.
    """
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # ---- USERS TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            device_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # ---- OTP TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS otp (
            id SERIAL PRIMARY KEY,
            phone TEXT UNIQUE NOT NULL,
            otp_code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL
        )
    """)
    conn.commit()

    # ---- CLIENTS TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            pan TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # ---- PORTFOLIOS TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            asset_type TEXT NOT NULL,
            asset_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            purchase_price REAL NOT NULL,
            current_price REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # ---- TRANSACTIONS TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # ---- FINANCIAL_PLANS TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS financial_plans (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            plan_type TEXT NOT NULL,
            goal_amount REAL NOT NULL,
            target_date DATE NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # ---- NOTIFICATIONS TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # ---- MARKET_DATA TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS market_data (
            id SERIAL PRIMARY KEY,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            volume BIGINT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # ---- REPORTS TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            report_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # ---- SYNC_LOGS TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sync_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            sync_type TEXT NOT NULL,
            status TEXT NOT NULL,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    cur.close()
    conn.close()
