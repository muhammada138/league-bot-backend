import math
from typing import Dict
from settings import DB_PATH
import sqlite3

ROLE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "TOP":     {"kda": .18, "csm": .25, "dpm": .18, "gpm": .10, "kp": .10, "vs": .04, "obj": .15},
    "JUNGLE":  {"kda": .15, "kp": .25, "obj": .30, "vs": .10, "dpm": .10, "gpm": .05, "csm": .05},
    "MID":     {"kda": .20, "dpm": .30, "kp": .15, "csm": .15, "gpm": .10, "vs": .05, "obj": .05},
    "ADC":     {"kda": .20, "dpm": .30, "csm": .25, "kp": .15, "gpm": .05, "vs": .05},
    "SUPPORT": {"kda": .15, "kp": .25, "vs": .30, "obj": .20, "dpm": .08, "gpm": .02},
}

def _percentile(cx, role: str, stat: str, val: float) -> float:
    col = "vision" if stat == "vs" else stat
    cur = cx.execute(f"SELECT {col} FROM performances WHERE role=? AND {col} IS NOT NULL", (role,))
    arr = [r[0] for r in cur.fetchall() if r[0] is not None]
    if not arr:
        return 0.5
    arr.sort()
    import bisect
    pos = bisect.bisect_left(arr, val)
    return pos / max(1, len(arr))

def soft_cap(x: float, cap: float) -> float:
    return cap * (1 - math.exp(-x / max(1e-9, cap)))

def compute_score_row(cx, role: str, k:int, a:int, d:int, csm:float, gpm:float, dpm:float, kp:float, vs:float, obj:float, win:bool) -> float:
    role = (role or "TOP").upper()
    weights = ROLE_WEIGHTS.get(role, ROLE_WEIGHTS["TOP"])
    kda = (k + a) / (d or 1)
    sig = {"kda": kda, "csm": csm, "gpm": gpm, "dpm": dpm, "kp": kp, "vs": vs, "obj": obj}
    p = {}
    for stat,val in sig.items():
        if val is None: 
            continue
        pr = _percentile(cx, role, stat, val)
        p[stat] = soft_cap(pr*2.2, 1.0)
    score = 0.0
    for s,w in weights.items():
        score += w * p.get(s, 0.0)
    score += 0.03 if win else -0.03
    return round(score*100, 2)
