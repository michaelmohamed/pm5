import os
import time

from loguru import logger

logger.info(f"Current Python process PID: {os.getpid()}")

while True:
    logger.info(f"{os.getpid()} - Running...")
    time.sleep(5)
