import pytest
from greengraph.importers.databases.inputoutput import useeio

# TODO add correct path to test data!
def test_format_useeio_matrices():
    try:
        dict_useeio = useeio.format_useeio_matrices(path_useeio="tests/importers/databases/test_data/useeio_test.csv")
    except:
        raise Exception("Error in formatting USEEIO matrices")
    

def test_useeio_matrices_to_greengraph():
    

def test_format_exiobase_matrices():
    pass