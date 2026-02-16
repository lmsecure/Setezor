import datetime
import os
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env.postgres', env_file_encoding='utf-8')
    postgres_user: str
    postgres_password: str
    postgres_db: str

class DEV:
    mode = os.environ.get("DEV_MODE", "False").lower() == "true"
    password = ""

if hasattr(sys, '_MEIPASS'):            # Nuitka/PyInstaller onefile
    BASE_PATH = sys._MEIPASS
elif getattr(sys, 'frozen', False):     # Nuitka standalone (no onefile)
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
PATH_PREFIX = os.path.join(os.path.expanduser('~'), '.local/share/setezor')

SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
HOST = os.environ.get("HOST", "0.0.0.0")
SERVER_REST_URL = os.environ.get("SERVER_REST_URL")
try:
    PORT = int(SERVER_REST_URL.rsplit(":")[-1])
except ValueError:
    PORT = os.environ.get("PORT", 16661)
ALGORITHM = "HS256"  # Алгоритм для подписи
ACCESS_TOKEN_EXPIRE_TIME = datetime.timedelta(days=7)
REFRESH_TOKEN_EXPIRE_TIME = datetime.timedelta(days=30)
INVITE_LINK_EXPIRE_TIME = datetime.timedelta(minutes=5)
COMMIT_STEP = 1000
LOG_LEVEL = "INFO"
if DEV.mode:
    LOG_LEVEL = "DEBUG"
LOG_DIR_PATH = os.path.join(PATH_PREFIX, 'logs')
TEMPLATES_DIR_PATH = os.path.join(BASE_PATH, 'pages/templates')
STATIC_FILES_DIR_PATH = os.path.join(BASE_PATH, 'pages/static/')
PROJECTS_DIR_PATH = os.path.abspath(os.path.join(PATH_PREFIX, 'projects'))
ALEMBIC_INI_PATH = os.path.join(BASE_PATH, "alembic.ini")
PASSWORD_HASH_ROUNDS = 600_000
ENGINE = os.environ.get("ENGINE", "sqlite")

if ENGINE == "sqlite":
    DB_URI = f"sqlite+aiosqlite:///{PATH_PREFIX}/db.sqlite3"
if ENGINE == "postgresql":
    pg_settings = PostgresSettings()
    DB_URI = f"postgresql+asyncpg://{pg_settings.postgres_user}:{pg_settings.postgres_password}@{os.environ.get("POSTGRES_HOST", "localhost")}:5432/{pg_settings.postgres_db}"
if not os.path.exists(PATH_PREFIX):
    os.makedirs(PATH_PREFIX, exist_ok=True)

if not os.path.exists(PROJECTS_DIR_PATH):
    os.makedirs(PROJECTS_DIR_PATH, exist_ok=True)

if not os.path.exists(LOG_DIR_PATH):
    os.makedirs(LOG_DIR_PATH, exist_ok=True)