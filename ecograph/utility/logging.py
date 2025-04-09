from contextlib import contextmanager
from datetime import datetime
import logging


@contextmanager
def logtimer(message):
    start_time = datetime.now()
    logging.info(f"{start_time.isoformat()}: Started {message}")
    try:
        yield
    finally:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logging.info(f"{end_time.isoformat()}: Completed in {duration}sec.: {message}")