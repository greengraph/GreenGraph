__version__ = "0.0.0"

from pathlib import Path
import tempfile
APP_CACHE_BASE_DIR = Path(tempfile.gettempdir()) / "greengraph"
