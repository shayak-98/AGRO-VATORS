import sqlite3
from pathlib import Path


# ============================================================
# DATABASE LOCATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_DIR = BASE_DIR / "database"

DATABASE_DIR.mkdir(
    exist_ok=True
)

DATABASE_PATH = DATABASE_DIR / "agrivise.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# CREATE TABLES
# ============================================================

def init_database():

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # SENSOR READINGS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

            temperature REAL,

            humidity REAL,

            soil INTEGER,

            distance REAL,

            pump TEXT,

            mode TEXT,

            latitude REAL,

            longitude REAL

        )
    """)


    connection.commit()

    connection.close()


# ============================================================
# SAVE SENSOR READING
# ============================================================

def save_sensor_reading(
    temperature,
    humidity,
    soil,
    distance,
    pump,
    mode,
    latitude=None,
    longitude=None
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        INSERT INTO sensor_readings (

            temperature,
            humidity,
            soil,
            distance,
            pump,
            mode,
            latitude,
            longitude

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        temperature,
        humidity,
        soil,
        distance,
        pump,
        mode,
        latitude,
        longitude

    ))


    connection.commit()

    connection.close()


# ============================================================
# GET SENSOR HISTORY
# ============================================================

def get_sensor_history(
    limit=100
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            timestamp,
            temperature,
            humidity,
            soil,
            distance,
            pump,
            mode,
            latitude,
            longitude

        FROM sensor_readings

        ORDER BY id DESC

        LIMIT ?
    """, (
        limit,
    ))


    rows = cursor.fetchall()

    connection.close()


    # Convert SQLite rows to dictionaries

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# TEST DATABASE
# ============================================================

if __name__ == "__main__":

    init_database()

    print(
        "AGRI-VISE database initialized."
    )

    print(
        f"Database location: {DATABASE_PATH}"
    )