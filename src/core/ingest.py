import os, json, time, sqlite3, pathlib, subprocess, shlex
from .db import _conn
from .scoring import compute_score_row

def _run_parser(rofl_path: str, json_path: str):
    cmd_tpl = os.getenv("PARSER_CMD", 'node parser/parse.js "{rofl}" "{json}"')
    cmd = cmd_tpl.format(rofl=rofl_path, json=json_path)
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Parser failed (code {proc.returncode}):\n{proc.stdout}")
    return json_path

def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return None

def ingest_rofl(rofl_path: str) -> int:
    tmp_json = rofl_path + ".json"
    _run_parser(rofl_path, tmp_json)
    meta = json.load(open(tmp_json, "r"))
    if os.path.exists(tmp_json):
        os.remove(tmp_json)

    game_id = meta.get("matchId") or meta.get("gameId") or str(int(time.time()*1000))

    with _conn() as cx:
        cx.execute("INSERT OR IGNORE INTO matches(game_id, created_at) VALUES(?, strftime('%s','now'))", (game_id,))
        mid = cx.execute("SELECT id FROM matches WHERE game_id=?", (game_id,)).fetchone()[0]

        participants = meta.get("participants") or meta.get("metadata", {}).get("participants") or meta.get("players", [])
        blue_kills = sum(p.get("kills",0) for p in participants[:5]) if len(participants)>=10 else 0
        red_kills  = sum(p.get("kills",0) for p in participants[5:10]) if len(participants)>=10 else 0
        time_min = max(1, int(meta.get("gameDuration", meta.get("duration", 1800))) // 60)

        for idx, p in enumerate(participants):
            team = "BLUE" if idx < 5 else "RED"
            puuid = p.get("puuid")
            summ  = p.get("summonerName") or p.get("name") or "Unknown"
            champ = p.get("championName") or p.get("champion") or "Unknown"
            role  = (p.get("individualPosition") or p.get("teamPosition") or p.get("role") or "TOP").upper()
            kills = int(p.get("kills", 0)); deaths = int(p.get("deaths", 0)); assists=int(p.get("assists", 0))
            cs    = (p.get("totalMinionsKilled") or 0) + (p.get("neutralMinionsKilled") or 0)
            csm   = cs / time_min
            gpm   = (_safe_float(p.get("goldEarned")) or 0) / time_min
            dpm   = (_safe_float(p.get("totalDamageDealtToChampions")) or 0) / time_min
            team_k = blue_kills if team=="BLUE" else red_kills
            kp    = ((kills+assists)*100.0/team_k) if team_k else None
            vs    = _safe_float(p.get("visionScore")) or _safe_float(p.get("visionScorePerMinute"))
            obj   = _safe_float(p.get("objectivesStolenAssists")) or _safe_float(p.get("objectiveScore"))
            win   = bool(p.get("win") or (p.get("stats",{}).get("win")))

            score = compute_score_row(cx, role, kills, assists, deaths, csm, gpm, dpm, kp, vs, obj, win)

            cx.execute("""INSERT INTO performances
            (match_id, team, puuid, summoner, riot_game_name, riot_tagline, champion, role,
             kills, deaths, assists, csm, gpm, dpm, kp, vision, objectives, win, perf_score)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
            (mid, team, puuid, summ, None, None, champ, role,
             kills, deaths, assists, csm, gpm, dpm, kp, vs, obj, 1 if win else 0, score))

    return mid

def ingest_dir(folder: str) -> int:
    count = 0
    for fn in sorted(os.listdir(folder)):
        if not fn.lower().endswith(".rofl"):
            continue
        path = os.path.join(folder, fn)
        try:
            ingest_rofl(path)
            count += 1
        except Exception as e:
            print("Ingest failed for", fn, ":", e)
    return count
