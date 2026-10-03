import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

app = Flask(__name__, static_folder="src", static_url_path="/src")

PAGE_SIZE = 20
CATEGORY_MAP = {"oneshots": 1, "ongoing": 2, "completed": 3}


# Supabase / Postgres connection
def get_connection():
    load_dotenv()
    conn = psycopg2.connect(
        database="postgres",
        user='postgres.bhixghvgnftcsplerlin',
        host='aws-0-us-east-1.pooler.supabase.com',
        port='6543',
        password=os.getenv("SUPABASE_PASS"),
        sslmode="require"
    )
    conn.set_client_encoding('UTF8')
    cur = conn.cursor()
    cur.execute("SET TIME ZONE 'America/New_York'")
    return conn


# Data access
def get_works_page(page_number=0, category_id=None, tag=None, keyword=None):
    offset = page_number * PAGE_SIZE
    keyword_pattern = f"%{keyword}%" if keyword else None
    tag_pattern = f"%{tag}%" if tag else None

    sql = """
        SELECT
            w.id, w.title, w.author, w.summary, w.chapter_count, w.current_chapter,
            w.completed, w.link, w.epub_download, w.published,
            s.id   AS series_id,
            s.title AS series_title,
            s.link  AS series_link,
            COALESCE(array_agg(DISTINCT ff.fandom) FILTER (WHERE ff.fandom IS NOT NULL), '{}') AS fandoms,
            COALESCE(array_agg(DISTINCT ft.tag) FILTER (WHERE ft.tag IS NOT NULL), '{}') AS tags,
            COALESCE(array_agg(DISTINCT fc.character) FILTER (WHERE fc.character IS NOT NULL), '{}') AS characters,
            COALESCE(array_agg(DISTINCT fr.relationship) FILTER (WHERE fr.relationship IS NOT NULL), '{}') AS relationships,
            COUNT(*) OVER() AS total_count
        FROM works w
        LEFT JOIN series s            ON s.id = w.series_id
        LEFT JOIN fic_fandoms ff      ON ff.fic_id = w.id
        LEFT JOIN fic_tags ft         ON ft.fic_id = w.id
        LEFT JOIN fic_characters fc   ON fc.fic_id = w.id
        LEFT JOIN fic_relationships fr ON fr.fic_id = w.id
        WHERE (%(category_id)s IS NULL OR w.filter_category_id = %(category_id)s)
          AND (%(keyword)s IS NULL OR w.title ILIKE %(keyword)s OR w.author ILIKE %(keyword)s)
          AND (%(tag)s IS NULL OR w.id IN (SELECT fic_id FROM fic_tags WHERE tag ILIKE %(tag)s))
        GROUP BY w.id, s.id
        ORDER BY w.date_added DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    params = {
        "category_id": category_id,
        "keyword": keyword_pattern,
        "tag": tag_pattern,
        "limit": PAGE_SIZE,
        "offset": offset,
    }

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    finally:
        conn.close()

    total = rows[0]["total_count"] if rows else 0
    return rows, total


def get_series_page(page_number=0, keyword=None):
    offset = page_number * PAGE_SIZE
    keyword_pattern = f"%{keyword}%" if keyword else None

    sql = """
        SELECT
            s.id, s.title, s.author, s.description, s.works_count, s.completed, s.link,
            COALESCE(
                json_agg(
                    json_build_object('work_title', sw.work_title, 'work_link', sw.work_link, 'position', sw.position)
                    ORDER BY sw.position
                ) FILTER (WHERE sw.work_id IS NOT NULL),
                '[]'
            ) AS works,
            COUNT(*) OVER() AS total_count
        FROM series s
        LEFT JOIN series_works sw ON sw.series_id = s.id
        WHERE (%(keyword)s IS NULL OR s.title ILIKE %(keyword)s OR s.author ILIKE %(keyword)s)
        GROUP BY s.id
        ORDER BY s.date_added DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    params = {"keyword": keyword_pattern, "limit": PAGE_SIZE, "offset": offset}

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    finally:
        conn.close()

    total = rows[0]["total_count"] if rows else 0
    return rows, total


def serialize_work(w):
    works_json = w["works"] if "works" in w else None  # not used here, just safety
    return {
        "id": w["id"],
        "type": "work",
        "title": w["title"],
        "author": w["author"],
        "summary": w["summary"],
        "chapter_count": w["chapter_count"],
        "current_chapter": w["current_chapter"],
        "completed": w["completed"],
        "link": w["link"],
        "epub_download": w["epub_download"],
        "published": w["published"],
        "fandoms": w["fandoms"] or [],
        "tags": w["tags"] or [],
        "characters": w["characters"] or [],
        "relationships": w["relationships"] or [],
        "series": (
            {"id": w["series_id"], "title": w["series_title"], "link": w["series_link"]}
            if w["series_id"] else None
        ),
    }


def serialize_series(s):
    works = s["works"]
    if isinstance(works, str):  # in case json comes back as text instead of parsed
        works = json.loads(works)
    return {
        "id": s["id"],
        "type": "series",
        "title": s["title"],
        "author": s["author"],
        "summary": s["description"],
        "works_count": s["works_count"],
        "completed": s["completed"],
        "link": s["link"],
        "works": works or [],
    }


# Routes
@app.route("/")
@app.route("/AO3.html")
def ao3_page():
    return render_template("AO3.html")


@app.route("/api/entries")
def api_entries():
    view = request.args.get("view", "all")
    page = request.args.get("page", default=0, type=int)
    tag = request.args.get("tag", "").strip() or None
    keyword = request.args.get("keyword", "").strip() or None

    if view == "series":
        rows, total = get_series_page(page, keyword=keyword)
        entries = [serialize_series(s) for s in rows]
    else:
        category_id = CATEGORY_MAP.get(view)
        rows, total = get_works_page(page, category_id=category_id, tag=tag, keyword=keyword)
        entries = [serialize_work(w) for w in rows]

    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    return jsonify({
        "entries": entries,
        "page": page,
        "page_size": PAGE_SIZE,
        "total_count": total,
        "total_pages": total_pages,
        "view": view,
    })


@app.route("/add-fic", methods=["POST"])
def add_fic():
    fic_url = request.form.get("fic_url", "").strip()
    # TODO: hand fic_url off to your scraper, insert into works/series
    return redirect(url_for("ao3_page"))


if __name__ == "__main__":
    app.run(debug=True)