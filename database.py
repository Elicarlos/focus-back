import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")

# Lê DATABASE_URL do ambiente ou tenta carregar do .env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL and os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.strip().startswith("DATABASE_URL="):
                SQLALCHEMY_DATABASE_URL = line.strip().split("DATABASE_URL=", 1)[1]
                if (SQLALCHEMY_DATABASE_URL.startswith('"') and SQLALCHEMY_DATABASE_URL.endswith('"')) or (SQLALCHEMY_DATABASE_URL.startswith("'") and SQLALCHEMY_DATABASE_URL.endswith("'")):
                    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL[1:-1]
                break

if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./focus_pragma.db"

# Exibe log com a URL mascarada por segurança
try:
    if "@" in SQLALCHEMY_DATABASE_URL:
        db_part = SQLALCHEMY_DATABASE_URL.split("@", 1)[1]
        user_part = SQLALCHEMY_DATABASE_URL.split("@", 1)[0]
        if ":" in user_part:
            scheme_user, _ = user_part.rsplit(":", 1)
            safe_url = f"{scheme_user}:***@{db_part}"
        else:
            safe_url = f"***@{db_part}"
    else:
        safe_url = SQLALCHEMY_DATABASE_URL
except Exception:
    safe_url = "URL de conexão (protegida)"

logger.info(f"Conectando ao banco de dados: {safe_url}")

# Ajuste específico para o driver assíncrono ou compatibilidade com postgresql
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
