import datetime
import os

BASE_PATH = '/'.join(__file__.split('/')[:-1])
PATH_PREFIX = os.path.join(os.path.expanduser('~'), '.local/share/setezor')
SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
ALGORITHM = "HS256"  # Алгоритм для подписи
ACCESS_TOKEN_EXPIRE_TIME = datetime.timedelta(days=7)
REFRESH_TOKEN_EXPIRE_TIME = datetime.timedelta(days=30)
INVITE_LINK_EXPIRE_TIME = datetime.timedelta(minutes=5)
COMMIT_STEP = 1000
LOG_LEVEL = "INFO"
DB_URI = f"sqlite+aiosqlite:///{PATH_PREFIX}/db.sqlite3"
TEMPLATES_DIR_PATH = os.path.join(BASE_PATH, 'pages/templates')
STATIC_FILES_DIR_PATH = os.path.join(BASE_PATH, 'pages/static/')
SSL_KEY_FILE_PATH = os.path.join(BASE_PATH, 'key.pem')
SSL_CERT_FILE_PATH = os.path.join(BASE_PATH, 'cert.pem')
PROJECTS_DIR_PATH = os.path.abspath(os.path.join(PATH_PREFIX, 'projects'))
ALEMBIC_INI_PATH = os.path.join(BASE_PATH, "alembic.ini")

if not os.path.exists(PATH_PREFIX):
    os.makedirs(PATH_PREFIX, exist_ok=True)

if not os.path.exists(PROJECTS_DIR_PATH):
    os.makedirs(PROJECTS_DIR_PATH, exist_ok=True)