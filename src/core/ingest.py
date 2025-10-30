import json
import os
import sqlite3
import subprocess
from .scoring import compute_perf_score


DB_PATH = "./data/keema.db"
PARSER_PATH = "./parser/parse.cjs"


# ----------------------------------------------------------------------
# Utility: database connection
# ----------------------------------------------------------------------
def _conn():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)


# ----------------------------------------------------------------------
# Utility: run Node parser
# ----------------------------------------------------------------------
def _run_parser(rofl_path: str, output_path: str):
    """Run the Node.js parser to convert .rofl → .json."""
    print(f"🚀 Starting parse for {rofl_path}")
    proc = subprocess.run(
        ["node", PARSER_PATH, rofl_path, output_path],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Parser failed (code {proc.returncode}):\n{proc.stdout}\n{proc.stderr}")
    print(f"✅ Parsed successfully: {rofl_path} → {output_path}\n")


# ----------------------------------------------------------------------
# Core: ingest a single ROFL file
# ----------------------------------------------------------------------
def ingest_rofl(rofl_path: str):
    """
    Ingest a .rofl replay file:
      1. Parses the file via Node.js parser.
      2. Extracts match and player stats.
      3. Inserts into SQLite DB (skips duplicates).
    """
    tmp_json = f"{rofl_path}.json"
    _run_parser(rofl_path, tmp_json)

    # Load parsed JSON
    with open(tmp_json, "r", encoding="utf-8") as f:
        meta = json.load(f)
    os.remove(tmp_json)

    # Get game ID
    match_id = meta.get("gameId") or meta.get("matchId") or os.path.basename(rofl_path)
    stats = meta.get("statsJson")

    # Determine stats structure
    if isinstance(stats, list):
        if len(stats) > 0 and isinstance(stats[0], dict) and "participants" in stats[0]:
            participants = stats[0]["participants"]
        else:
            participants = stats
    elif isinstance(stats, dict):
        participants = stats.get("participants", [])
    else:
        participants = []

    if not participants:
        raise RuntimeError("No participants found in metadata")

    # Store in database
    with _conn() as cx:
        cx.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT UNIQUE
            )
        """)
        cx.execute("""
            CREATE TABLE IF NOT EXISTS performances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                summoner TEXT,
                riot_game_name TEXT,
                champion TEXT,
                kills INTEGER,
                deaths INTEGER,
                assists INTEGER,
                win INTEGER,
                perf_score REAL,
                FOREIGN KEY(match_id) REFERENCES matches(id)
            )
        """)

        # Skip duplicate matches
        existing = cx.execute("SELECT id FROM matches WHERE game_id = ?", (match_id,)).fetchone()
        if existing:
            print(f"⚠️ Skipping duplicate match: {match_id}")
            return match_id

        # Insert match
        cx.execute("INSERT INTO matches (game_id) VALUES (?)", (match_id,))
        mid = cx.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Insert player stats
        for p in participants:
            summoner = (
                p.get("riotIdGameName")
                or p.get("riotId")
                or p.get("summonerName")
                or "Unknown"
            )

            perf = compute_perf_score(p)
            cx.execute(
                """
                INSERT INTO performances
                (match_id, summoner, riot_game_name, champion, kills, deaths, assists, win, perf_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mid,
                    summoner,
                    p.get("riotIdGameName"),
                    p.get("championName"),
                    p.get("kills", 0),
                    p.get("deaths", 0),
                    p.get("assists", 0),
                    1 if p.get("win") else 0,
                    perf,
                ),
            )

    print(f"✅ Ingested match {match_id} successfully!")
    return match_id


# ----------------------------------------------------------------------
# Optional: batch ingest
# ----------------------------------------------------------------------
def ingest_dir(folder: str = "./data/pending"):
    """Ingest all .rofl files in a folder."""
    for file in os.listdir(folder):
        if file.endswith(".rofl"):
            try:
                ingest_rofl(os.path.join(folder, file))
            except Exception as e:
                print(f"❌ Failed to ingest {file}: {e}")
