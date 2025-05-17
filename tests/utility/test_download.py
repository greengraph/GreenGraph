import pytest
from greengraph.utility.download import _load_file_from_zenodo_with_caching
from greengraph import remove_cache_dir

def test_real_zenodo_download_and_caching():
    """
    Tests the _load_file_from_zenodo_with_caching function by:
    
    1. Downloading a known public test file from Zenodo.
    2. Verifying its content.
    3. Calling the function again for the same file.
    4. Verifying that the file is served from cache (by checking modification time).

    References
    ----------
    [Zenodo "Test File"](https://doi.org/10.5281/zenodo.13242884)
    """
    zenodo_record_id = "13242885"
    file_name_on_zenodo = "test1.txt"
    expected_content_substring = b"testets"
    cache_subdirectory = "my_test_cache_dir"

    dict_testfile = _load_file_from_zenodo_with_caching(
        name_file=file_name_on_zenodo,
        name_dir_cache=cache_subdirectory,
        zenodo_record=zenodo_record_id,
    )

    # Check if the file exists and has the expected content
    with open(dict_testfile['path_cached_file'], "rb") as f:
        content = f.read()
    assert expected_content_substring in content

    # Check if the file is served from cache upon re-download
    dict_testfile2 = _load_file_from_zenodo_with_caching(
        name_file=file_name_on_zenodo,
        name_dir_cache=cache_subdirectory,
        zenodo_record=zenodo_record_id,
    )
    assert dict_testfile['path_cached_file'] == dict_testfile2['path_cached_file']
    assert dict_testfile['path_cached_file'].stat().st_mtime == dict_testfile2['path_cached_file'].stat().st_mtime
    
    remove_cache_dir()