import os
from fastapi.templating import Jinja2Templates
from setezor.settings import TEMPLATES_DIR_PATH


TEMPLATES_DIR = Jinja2Templates(directory=TEMPLATES_DIR_PATH)