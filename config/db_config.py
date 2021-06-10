import os
import logging

logger = logging.getLogger(__name__)

ENGINE_STRING = os.environ.get('ENGINE_STRING')
DOCKER_CONTAINER = os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False)

if DOCKER_CONTAINER:
    logger.info("using docker container")
else:
    logger.info("not using docker container")

if ENGINE_STRING is not None:
    logger.info(f'using env variable $ENGINE_STRING to connect to db')
else:
    logger.info(f'using filepath sqlite:///data/entries.db as engine string')
    ENGINE_STRING = 'sqlite:///data/entries.db'
