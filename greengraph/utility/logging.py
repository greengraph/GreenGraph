from contextlib import contextmanager
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO, 
    format='greengraph | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler()]  # Output to console
)

@contextmanager
def logtimer(message):
    start_time = datetime.now()
    logging.info(f"{start_time.strftime('%H:%M:%S')}: Started {message}")
    try:
        yield
    finally:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        minutes, seconds = divmod(duration, 60)
        logging.info(f"{end_time.strftime('%H:%M:%S')}: Completed {message} ({int(minutes):02d}:{int(seconds):02d} min:sec)")