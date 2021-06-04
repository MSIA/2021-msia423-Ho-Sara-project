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
AWS_ENGINE_STRING = os.environ.get('AWS_ENGINE_STRING')
DOCKER_CONTAINER = os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False)
if DOCKER_CONTAINER or (AWS_ENGINE_STRING is not None):
    logger.info(f'connecting to `AWS_ENGINE_STRING`')
    SQLALCHEMY_DATABASE_URI = AWS_ENGINE_STRING
else:
    logger.info(f'connecting to local entries.db')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///data/entries.db'
