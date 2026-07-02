import pandas as pd
import flask

@app.route('/add-anime', methods=['POST'])
def add_anime():
    title = request.form.get('title', '').strip()
    if not title:
        return jsonify({"error": "Title required"}), 400

    season = request.form.get('season', '').strip() or "Season 1"
    episodes = request.form.get('episodes', '').strip() or "? episodes"
    status = request.form.get('status', 'In Progress')
    image = request.form.get('image', '').strip()
    edit_id = request.form.get('edit_id')

    conn = get_db_connection()
    cur = conn.cursor()

    if edit_id:
        cur.execute("""
            UPDATE anime SET title=%s, season=%s, episodes=%s, status=%s, image=%s
            WHERE id=%s
        """, (title, season, episodes, status, image, edit_id))
    else:
        cur.execute("""
            INSERT INTO anime (title, season, episodes, status, image)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, season, episodes, status, image))

    conn.commit()
    cur.execute("SELECT id, title, season, episodes, status, image FROM anime ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    entries = [dict(zip(['id','title','season','episodes','status','image'], r)) for r in rows]
    print(entries)
    return jsonify({"entries": entries})
    
    
if __name__ == "__main__":
    main()
