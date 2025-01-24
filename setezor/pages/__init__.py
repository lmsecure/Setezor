import os
from fastapi.templating import Jinja2Templates
from setezor.setezor import base_path


TEMPLATES_DIR = Jinja2Templates(directory=os.path.join(base_path, 'pages/templates'))