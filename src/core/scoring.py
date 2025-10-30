# src/core/scoring.py

def compute_perf_score(p):
    """
    Compute a simple performance score based on KDA, CS, damage, and vision.
    Designed to work even when some fields are missing.
    """
    kills = p.get("kills", 0)
    deaths = p.get("deaths", 0)
    assists = p.get("assists", 0)
    cs = p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0)
    dmg = p.get("totalDamageDealtToChampions", 0)
    vision = p.get("visionScore", 0)

    # Base KDA ratio (avoid divide by zero)
    kda = (kills + assists) / (deaths if deaths > 0 else 1)

    # Weighted score components
    score = (
        kda * 10
        + (cs / 10)
        + (dmg / 1000)
        + (vision / 5)
    )

    # Cap to prevent outliers
    return round(min(score, 100.0), 2)
