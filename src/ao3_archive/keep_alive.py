import os
import time
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

while True:
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")

        print("Supabase database is active.", file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))

    except Exception as e:
        print(f"Database ping failed: {e}", file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"))

    time.sleep(3600)