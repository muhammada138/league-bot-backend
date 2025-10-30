import os, sqlite3, pathlib
from settings import DB_PATH

def _conn():
    pathlib.Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(DB_PATH)
    cx.row_factory = sqlite3.Row
    return cx

async def init_db():
    with _conn() as cx:
        cx.executescript("""
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT UNIQUE,
    created_at INTEGER
);
CREATE TABLE IF NOT EXISTS performances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    team TEXT,
    puuid TEXT,
    summoner TEXT,
    riot_game_name TEXT,
    riot_tagline TEXT,
    champion TEXT,
    role TEXT,
    kills INTEGER, deaths INTEGER, assists INTEGER,
    csm REAL, gpm REAL, dpm REAL, kp REAL, vision REAL, objectives REAL,
    win INTEGER,
    perf_score REAL
);
CREATE INDEX IF NOT EXISTS idx_perf_match ON performances(match_id);
CREATE INDEX IF NOT EXISTS idx_perf_puuid ON performances(puuid);
""")
