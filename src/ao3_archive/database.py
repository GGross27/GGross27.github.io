import psycopg2
from dotenv import load_dotenv
import os
import datetime

def get_connection():
    load_dotenv()
    # Fetch variables
    # DATABASE_URL = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(
        database="postgres",
        user='postgres.bhixghvgnftcsplerlin',
        host= 'aws-0-us-east-1.pooler.supabase.com',
        port='6543',
        password=os.getenv("SUPABASE_PASS"),
        sslmode="require"
    )
    conn.set_client_encoding('UTF8')
    
    cur = conn.cursor()
    cur.execute("SET TIME ZONE 'America/New_York'")
    return conn

# def get_connection():
#     password = os.getenv('PSQL_PASS')
    
#     conn = psycopg2.connect(
#         database="schema",
#         user='postgres',
#         password=password,
#         host='localhost'
#         # port= '5432'
#     )
#     return conn
    
def upsert_work(work: dict):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO works (id, title, author, summary, chapter_count, current_chapter,
                            completed, series_id, filter_category_id, link,
                            epub_download, status, published, status_date, date_added, last_scraped)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
        ON CONFLICT (id) DO UPDATE SET
            chapter_count = EXCLUDED.chapter_count,
            completed = EXCLUDED.completed,
            filter_category_id = EXCLUDED.filter_category_id,
            status = EXCLUDED.status, 
            status_date = EXCLUDED.status_date,
            last_scraped = NOW()
    """, (
        work['ID'], work['Title'], work['Author'], work['Summary'],
        work['Chapter Count'], work['Current Chapter'], work['Completed'], 
        work['Series_id'], work['Category_ID'], work['url'], work['download'], 
        'active', work["Published"], work["Status Date"]
    ))
    
    try: 
        cur.execute("BEGIN")
        
        cur.execute("DELETE FROM fic_tags          WHERE fic_id = %s", (work['ID'],))
        cur.execute("DELETE FROM fic_fandoms       WHERE fic_id = %s", (work['ID'],))
        cur.execute("DELETE FROM fic_characters    WHERE fic_id = %s", (work['ID'],))
        cur.execute("DELETE FROM fic_relationships WHERE fic_id = %s", (work['ID'],))

        for fandom in work['Fandom Tags']:
            cur.execute("INSERT INTO fic_fandoms (fic_id, fandom) VALUES (%s,%s)", 
                        (work['ID'], fandom))
        for tag in work['Additional Tags']:
            cur.execute("INSERT INTO fic_tags (fic_id, tag) VALUES (%s,%s)", 
                        (work['ID'], tag))
        for character in work['Character Tags']:
            cur.execute("INSERT INTO fic_characters (fic_id, character) VALUES (%s,%s)", 
                        (work['ID'], character))   
        for relationship in work['Relationship Tags']:
            cur.execute("INSERT INTO fic_relationships (fic_id, relationship) VALUES (%s,%s)", 
                        (work['ID'], relationship))
        
        cur.execute("COMMIT")
    except Exception as e:
        cur.execute("ROLLBACK")  # undo everything if anything fails
        print(f"[{datetime.datetime.now()}] -- Transaction failed, rolled back: {e}", file=open("src/logs/ao3_scraper_log.txt", "a", encoding="utf-8"), file2=open("src/logs/database_log.txt", "a", encoding="utf-8"))

    conn.commit()
    cur.close()
    conn.close()
    
def upsert_series(series: dict):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO series (id, title, author, description, notes, works_count, completed, link, 
                            filter_category_id, status, created, updated, date_added, last_scraped)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
        ON CONFLICT (id) DO UPDATE SET
            description = EXCLUDED.description,
            notes = EXCLUDED.notes,
            works_count = EXCLUDED.works_count,
            completed = EXCLUDED.completed,
            created = EXCLUDED.created,
            updated = EXCLUDED.updated,
            filter_category_id = EXCLUDED.filter_category_id,
            status = EXCLUDED.status, 
            last_scraped = NOW()
    """, (
        series['ID'], series['Title'], series['Author'], series['Description'], 
        series['Notes'], series['Works Count'], series['Completed'], 
        series['url'], series['Category_ID'], 'active', series['Created'], series['Updated']  
    ))
    
    cur.execute("DELETE FROM series_works WHERE series_id = %s", (series['ID'],))
    for i, work in enumerate(series['Works List']):
        cur.execute("""
            INSERT INTO series_works (series_id, work_id, work_title, work_link, position)
            VALUES (%s,%s,%s,%s,%s)
        """, (series['ID'], work['work_id'], work['work_title'], work['work_link'], i+1))
        
    conn.commit()
    cur.close()
    conn.close()
    
    
def insert_failed_link(url, id=None, status_code=None, error_msg=None):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO failed_links (id, url, status_code, error_msg, attempted)
        VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT (url) DO UPDATE SET
            id          = EXCLUDED.id,
            status_code = EXCLUDED.status_code,
            error_msg   = EXCLUDED.error_msg,
            attempted   = NOW(),
            resolved    = false
    """, (id, url, status_code, error_msg))
    
    conn.commit()
    cur.close()
    conn.close()
    
def resolve_failed_link(url):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE failed_links
        SET resolved = TRUE,
            status_code = NULL,
            error_msg = NULL
        WHERE url = %s
    """, (url,))

    conn.commit()
    cur.close()
    conn.close()