import logging

logging.basicConfig(
    level=logging.INFO, 
    format='greengraph | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler()]  # Output to console
)

__version__ = "0.0.0"

from pathlib import Path
import tempfile
import shutil

APP_CACHE_BASE_DIR = Path(tempfile.gettempdir()) / "greengraph"

def remove_cache_dir():
    """Removes the application cache directory."""
    if APP_CACHE_BASE_DIR.exists():
        try:
            shutil.rmtree(APP_CACHE_BASE_DIR)
            logging.info(f"Cache directory {APP_CACHE_BASE_DIR} removed successfully.")
        except OSError as e:
            logging.error(f"Error removing cache directory {APP_CACHE_BASE_DIR}: {e}")
    else:
        logging.info(f"Cache directory {APP_CACHE_BASE_DIR} does not exist. Nothing to remove.")


def cache_dir_path():
    """Returns the path to the application cache directory."""
    if not APP_CACHE_BASE_DIR.exists():
        logging.info(f"No cache directory exists. This directory is created only by some download functions.")
        return None
    else:
        logging.info(f"Cache directory located at: {APP_CACHE_BASE_DIR}.")
        return APP_CACHE_BASE_DIR