import logging
from contextlib import contextmanager
from datetime import datetime


@contextmanager
def logtimer(message):
    start_time = datetime.now()
    logging.info(f"{start_time.strftime('%H:%M:%S')}: Started {message}")
    
    operation_succeeded = False
    try:
        yield
        operation_succeeded = True
    finally:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        minutes, seconds = divmod(duration, 60)
        
        if operation_succeeded:
            logging.info(f"{end_time.strftime('%H:%M:%S')}: Completed {message} ({int(minutes):02d}:{int(seconds):02d} min:sec)")
        else:
            logging.error(f"{end_time.strftime('%H:%M:%S')}: Failed {message} after ({int(minutes):02d}:{int(seconds):02d} min:sec)")