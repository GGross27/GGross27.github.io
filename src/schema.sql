-- Filter category lookup (4 fixed rows, populated once)
CREATE TABLE filter_categories (
    id               INT PRIMARY KEY,
    label            TEXT NOT NULL,   -- 'Oneshot','Ongoing','Completed','Series'
    min_chapters     INT,
    completed        BOOLEAN,
    series_present   BOOLEAN
);

-- Main works table
CREATE TABLE works (
    id                 VARCHAR(20) PRIMARY KEY,
    title              TEXT NOT NULL,
    author             TEXT,                     -- from "Author"
    summary            TEXT,
    chapter_count      INT,
    current_chapter    INT DEFAULT 1,            -- from "Current Chapter"
    completed          BOOLEAN DEFAULT false,
    series_id          VARCHAR(20),
    filter_category_id INT REFERENCES filter_categories(id),
    link               TEXT,
    epub_download      TEXT,                     -- from "download"
    local_file         TEXT,                     -- for stored epub path
    status             TEXT DEFAULT 'active',
    date_added         TIMESTAMP DEFAULT NOW(),
    last_scraped       TIMESTAMP
);

-- Main Series table
CREATE TABLE series(
    id                 VARCHAR(20) PRIMARY KEY,  -- AO3S_xxxxxxx
    title              TEXT NOT NULL,
    author             TEXT,
    works_count        INT,                      -- from "Works Count"
    completed          BOOLEAN DEFAULT false,
    link               TEXT,
    filter_category_id INT REFERENCES filter_categories(id),
    status             TEXT DEFAULT 'active',
    date_added         TIMESTAMP DEFAULT NOW(),
    last_scraped       TIMESTAMP
);
-- Junction tables (one row per tag/character/relationship per fic)
CREATE TABLE fic_tags          (fic_id VARCHAR(20) REFERENCES works(id) ON DELETE CASCADE, tag TEXT);
CREATE TABLE fic_characters    (fic_id VARCHAR(20) REFERENCES works(id) ON DELETE CASCADE, character TEXT);
CREATE TABLE fic_relationships (fic_id VARCHAR(20) REFERENCES works(id) ON DELETE CASCADE, relationship TEXT);


CREATE TABLE anime (
    id              VARCHAR(20) PRIMARY KEY,  -- e.g. ANI_xxxxxxx
    title           TEXT NOT NULL,
    current_season  INT DEFAULT 1,
    total_seasons   INT,
    episodes        INT,                      -- total known episodes
    current_ep      INT DEFAULT 0,            -- how far you've watched
    status          TEXT,                     -- 'Watched', 'In Progress', 'Later'
    cover_url       TEXT,
    date_added      TIMESTAMP DEFAULT NOW()
);


CREATE TABLE manhwa (
    id            VARCHAR(20) PRIMARY KEY,  -- e.g. MAN_xxxxxxx
    title         TEXT NOT NULL,
    chapters      INT,                      -- total known chapters
    current_ch    INT DEFAULT 0,            -- how far you've read
    status        TEXT,                     -- 'Completed', 'In Progress', 'Later'
    cover_url     TEXT,
    date_added    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE media_tags (
    media_id    VARCHAR(20),  -- references either anime.id or manhwa.id
    media_type  TEXT,         -- 'anime' or 'manhwa' so you know which table
    tag         TEXT
);