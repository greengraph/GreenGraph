# %%
import pytest
from importlib import resources
from greengraph.importers.databases.inputoutput import (
    useeio,
    exiobase
)

def test_format_useeio_matrices():
    try:
        path_useeio_fixture = resources.files('tests.fixtures.databases').joinpath('fixture_USEEIOv2.0.1-411.xlsx')
        dict_useeio = useeio.format_useeio_matrices(path_useeio=path_useeio_fixture)
    except:
        raise Exception("Error in formatting USEEIO matrices")
    

def test_format_exiobase_matrices():
    try:
        path_exiobase_fixture = resources.files('tests.fixtures.databases').joinpath('fixture_IOT_2014_pxp.zip')
        dict_exiobase_files  = exiobase.unpack_exiobase_zip(path_zip=path_exiobase_fixture)
        dict_exiobase = exiobase.format_exiobase_matrices(
            path_A=dict_exiobase_files['path_A'],
            path_S=dict_exiobase_files['path_S'],
            path_S_metadata=dict_exiobase_files['path_S_metadata'],
        )
    except:
        raise Exception("Error in formatting USEEIO matrices")