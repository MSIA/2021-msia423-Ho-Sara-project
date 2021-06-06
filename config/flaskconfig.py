import os
import logging

logger = logging.getLogger(__name__)

DEBUG = True
LOGGING_CONFIG = "config/logging/local.conf"
PORT = 5000
APP_NAME = "wikinews"
SQLALCHEMY_TRACK_MODIFICATIONS = True
HOST = "0.0.0.0"
SQLALCHEMY_ECHO = False  # If true, SQL for queries made will be printed
MAX_ROWS_SHOW = 100

# Connection string
ENGINE_STRING = os.environ.get('ENGINE_STRING')
DOCKER_CONTAINER = os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False)

if DOCKER_CONTAINER or (ENGINE_STRING is not None) or (ENGINE_STRING == ''):
    logger.info(f'using env variable $ENGINE_STRING to connect to db')
else:
    logger.info(f'using filepath sqlite:///data/entries.db as engine string')
    ENGINE_STRING = 'sqlite:///data/entries.db'
