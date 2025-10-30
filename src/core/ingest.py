import os, subprocess, json, sqlite3
from .db import _conn
from .scoring import compute_perf_score

def _run_parser(rofl_path: str, out_json: str):
    result = subprocess.run(
        ["node", "parser/parse.cjs", rofl_path, out_json],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Parser failed (code {result.returncode}):\n{result.stdout}\n{result.stderr}")

def ingest_rofl(rofl_path: str):
    tmp_json = f"{rofl_path}.json"
    _run_parser(rofl_path, tmp_json)
    with open(tmp_json, "r", encoding="utf-8") as f:
        meta = json.load(f)
    os.remove(tmp_json)

    match_id = meta.get("gameId")
    participants = meta["statsJson"]["participants"]
    with _conn() as cx:
        cx.execute("INSERT INTO matches (game_id) VALUES (?)", (match_id,))
        mid = cx.execute("SELECT last_insert_rowid()").fetchone()[0]
        for p in participants:
            perf = compute_perf_score(p)
            cx.execute(
                """INSERT INTO performances 
                (match_id, summoner, riot_game_name, champion, kills, deaths, assists, win, perf_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    mid,
                    p.get("summonerName"),
                    p.get("riotIdGameName"),
                    p.get("championName"),
                    p.get("kills", 0),
                    p.get("deaths", 0),
                    p.get("assists", 0),
                    1 if p.get("win") else 0,
                    perf,
                )
            )
    return match_id

def ingest_dir(directory: str):
    count = 0
    for f in os.listdir(directory):
        if f.endswith(".rofl"):
            path = os.path.join(directory, f)
            ingest_rofl(path)
            count += 1
    return count
