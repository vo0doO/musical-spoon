import sys

from loguru import logger

logger.remove()
logger.add(sink=sys.stdout, level='DEBUG', colorize=True)
