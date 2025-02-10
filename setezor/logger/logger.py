import sys
import os
from loguru import logger
from setezor.settings import PATH_PREFIX, LOG_LEVEL

logger.remove()  # Remove default handler
logger.add(sys.stdout, level=LOG_LEVEL)
logger.add(os.path.join(PATH_PREFIX, "log.json"),
           level=LOG_LEVEL,
           format="{message}",
           serialize=True)
