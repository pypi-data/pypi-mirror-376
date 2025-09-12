# -*- coding: utf-8 -*-
import logging
import os
from dotenv import load_dotenv

load_dotenv()
log_level = os.environ.get("LOG_LEVEL", logging.DEBUG)

logger = logging.getLogger("app")
logger.setLevel(log_level)
