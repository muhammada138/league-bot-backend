from fastapi import FastAPI, UploadFile, HTTPException, Header, File
from fastapi.middleware.cors import CORSMiddleware
from settings import ALLOWED_ORIGINS, ADMIN_KEY, DB_PATH, SB_GAMMA, PENDING_DIR, APPROVED_DIR
from src.core.db import _conn, init_db
from src.core.ingest import ingest_rofl, ingest_dir
import os, math, shutil, sqlite3

app = FastAPI(title="Keema Scores API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://muhammada138.github.io",  # your GitHub Pages frontend
        "http://localhost:8000",           # optional for local tests
        "http://127.0.0.1:5500",           # optional for local Live Server
        "https://league-bot-backend.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup():
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(APPROVED_DIR, exist_ok=True)
    await init_db()

def _require_admin(x_admin_key: str | None):
    if not x_admin_key or x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

@app.get("/scoreboard")
def scoreboard():
    with _conn() as cx:
        rows = cx.execute("""
            SELECT
                COALESCE(riot_game_name, summoner, 'Unknown') AS name,
                COUNT(*) AS games,
                AVG((kills+assists)*1.0/CASE WHEN deaths=0 THEN 1 ELSE deaths END) AS kda,
                AVG(perf_score) AS score,
                AVG(win*100.0) AS wr
            FROM performances
            GROUP BY COALESCE(riot_game_name, summoner)
            ORDER BY score DESC
        """).fetchall()
        rows = [dict(r) for r in rows]
        if not rows:
            return {"rows": [], "avg_games": 0}
        avg_games = sum(r["games"] for r in rows) / len(rows)
        GAMMA = SB_GAMMA
        out = []
        for r in rows:
            penalty = math.exp(-max(0.0, r["games"] / max(1.0, avg_games)) * GAMMA)
            adj = r["score"] * (0.75 + 0.25 * (1 - penalty))
            out.append({"name": r["name"], "games": r["games"], "wr": round(r["wr"] or 0,1), "kda": round(r["kda"] or 0,2), "score": round(adj or 0,2)})
        out.sort(key=lambda x: x["score"], reverse=True)
        return {"rows": out, "avg_games": avg_games}

@app.get("/champions")
def champions():
    with _conn() as cx:
        rows = cx.execute("""
            SELECT champion,
                   COUNT(*) AS games,
                   AVG((kills+assists)*1.0/CASE WHEN deaths=0 THEN 1 ELSE deaths END) AS kda,
                   AVG(perf_score) AS score
            FROM performances
            GROUP BY champion
            ORDER BY score DESC
        """).fetchall()
        rows = [dict(r) for r in rows]
        if not rows:
            return {"rows": []}
        avg_games = sum(r["games"] for r in rows) / len(rows)
        out = []
        for r in rows:
            penalty = math.exp(-max(0.0, r["games"] / max(1.0, avg_games)) * SB_GAMMA)
            adj = r["score"] * (0.75 + 0.25 * (1 - penalty))
            out.append({"champion": r["champion"], "games": r["games"], "kda": round(r["kda"] or 0,2), "score": round(adj or 0,2)})
        return {"rows": out, "avg_games": avg_games}

@app.get("/game/{idx}")
def game(idx: int):
    with _conn() as cx:
        m = cx.execute("SELECT id, game_id, created_at FROM matches ORDER BY id DESC LIMIT 1 OFFSET ?", (idx-1,)).fetchone()
        if not m:
            raise HTTPException(status_code=404, detail="Game not found")
        rows = cx.execute("SELECT * FROM performances WHERE match_id=? ORDER BY team, perf_score DESC", (m["id"],)).fetchall()
        return {"match": dict(m), "performances": [dict(r) for r in rows]}

@app.post("/upload")
async def upload(file: UploadFile = File(...), x_admin_key: str | None = Header(None)):
    _require_admin(x_admin_key)
    if not file.filename.lower().endswith(".rofl"):
        raise HTTPException(status_code=400, detail="Only .rofl files allowed")
    tmp_path = os.path.join(PENDING_DIR, file.filename)
    with open(tmp_path, "wb") as f:
        f.write(await file.read())
    match_id = ingest_rofl(tmp_path)
    shutil.move(tmp_path, os.path.join(APPROVED_DIR, os.path.basename(tmp_path)))
    return {"status": "ok", "match_id": match_id}

@app.post("/refresh")
def refresh(x_admin_key: str | None = Header(None)):
    _require_admin(x_admin_key)
    n = ingest_dir(APPROVED_DIR)
    return {"status": "ok", "ingested": n}
