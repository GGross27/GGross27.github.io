import psycopg2
import os

def get_connection():
    password = os.getenv('PSQL_PASS')
    
    conn = psycopg2.connect(
        database="schema",
        user='postgres',
        password=password,
        host='localhost'
        # port= '5432'
    )
    return conn
    
def upsert_work(work: dict):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO works (id, title, author, summary, chapter_count, current_chapter,
                            completed, series_id, filter_category_id, link,
                            epub_download, status, date_added, last_scrape)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
        ON CONFLICT (id) DO UPDATE SET
            chapter_count = EXCLUDED.chapter_count,
            completed = EXCLUDED.completed,
            filter_category_id = EXCLUDED.filter_category_id,
            status = EXCLUDED.status, 
            last_scraped = NOW()
    """, (
        work['ID'], work['Title'], work['Author'], work['Summary'],
        work['Chapter Count'], work['Current Chapter'], work['Completed'], 
        work['Series_id'], work['Category_ID'], work['url'], work['download'], 'active' 
    ))
    
    cur.execute("DELETE FROM fic_tags          WHERE fic_id = %s", (work['ID'],))
    cur.execute("DELETE FROM fic_fandoms       WHERE fic_id = %s", (work['ID'],))
    cur.execute("DELETE FROM fic_characters    WHERE fic_id = %s", (work['ID'],))
    cur.execute("DELETE FROM fic_relationships WHERE fic_id = %s", (work['ID'],))

    for tag in work['Fandom Tags']:
        cur.execute("INSERT INTO fic_fandoms (fic_id, fandom) VALUES (%s,%s)", 
                    (work['ID'], fandom))
    for tag in work['Additional Tags']:
        cur.execute("INSERT INTO fic_tags (fic_id, tag) VALUES (%s,%s)", 
                    (work['ID'], tag))
    for tag in work['Charaters Tags']:
        cur.execute("INSERT INTO fic_characters (fic_id, character) VALUES (%s,%s)", 
                    (work['ID'], character))   
    for tag in work['Relationship Tags']:
        cur.execute("INSERT INTO fic_relationships (fic_id, relationship) VALUES (%s,%s)", 
                    (work['ID'], relationship))
    
    conn.commit()
    cur.close()
    conn.close()
    
def upsert_series(series: dict):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO series (id, title, author, works_count, completed, link, 
                            filter_category_id, status, date_added, last_scrape)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
        ON CONFLICT (id) DO UPDATE SET
            work_count = EXCLUDED.work_count,
            completed = EXCLUDED.completed,
            filter_category_id = EXCLUDED.filter_category_id,
            status = EXCLUDED.status, 
            last_scraped = NOW()
    """, (
        series['ID'], series['Title'], series['Author'], series['Works Count'],
        series['Completed'], series['url'], series['Category_ID'], 'active' 
    ))
    
    conn.commit()
    cur.close()
    conn.close()