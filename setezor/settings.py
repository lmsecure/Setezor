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