import os

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
ADMIN_KEY = os.getenv("ADMIN_KEY", "keema-1234")
BASE_DIR     = os.getenv("BASE_DIR", ".")
DATA_DIR     = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
PENDING_DIR  = os.getenv("PENDING_DIR", os.path.join(DATA_DIR, "pending"))
APPROVED_DIR = os.getenv("APPROVED_DIR", os.path.join(DATA_DIR, "approved"))
DB_PATH      = os.getenv("DB_PATH", os.path.join(DATA_DIR, "lolscores.db"))
SB_GAMMA = float(os.getenv("SB_GAMMA", "1.0"))
