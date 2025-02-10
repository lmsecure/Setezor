import os
from fastapi.templating import Jinja2Templates
from setezor.settings import BASE_PATH


TEMPLATES_DIR = Jinja2Templates(directory=os.path.join(BASE_PATH, 'pages/templates'))