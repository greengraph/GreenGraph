import requests
from pathlib import Path
from greengraph.utility.logging import logtimer
import logging
from greengraph import APP_CACHE_BASE_DIR


def _load_file_from_zenodo_with_caching(
    name_file: str,
    name_dir_cache: str,
    zenodo_record: str,
) -> dict[str, Path]:
    r"""
    Given a file name, a directory name, and a Zenodo record ID,
    downloads the file from Zenodo and caches it locally.
    If the file already exists in the local cache, it is used directly.

    Parameters
    ----------
    name_file : str
        Name of the file, as it is stored on Zenodo.
    name_dir_cache : str
        Name of the temporary directory into which the file will be saved.  
        This is a subdirectory of the GreenGraph main `APP_CACHE_BASE_DIR`,
        which is set in `greengraph/__init__.py`.
    zenodo_record : str
        Zenodo record ID.  
        For example (the integer part): `https://zenodo.org/records/15272306`.

    Returns
    -------
    Path
        Path to the downloaded/cached file.
    """
    
    path_dir_cache = APP_CACHE_BASE_DIR / name_dir_cache
    path_dir_cache.mkdir(parents=True, exist_ok=True)
    path_cached_file = path_dir_cache / name_file

    if path_cached_file.exists():
        logging.info(f"Found file {name_file} in local cache.")
        file = path_cached_file
    else:
        with logtimer(f"downloading file {name_file} from Zenodo."):
            url_download = f"https://zenodo.org/records/{zenodo_record}/files/{name_file}?download=1"
            download = requests.get(url_download, timeout=30)
            download.raise_for_status()
            with open(path_cached_file, "wb") as f_cache:
                f_cache.write(download.content)
                file = path_cached_file

    return {
        "path_cached_file": path_cached_file,
        "path_dir_cache": path_dir_cache
    }