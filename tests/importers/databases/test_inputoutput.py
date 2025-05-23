# %%
import pytest
import numpy as np
from importlib import resources
from greengraph.importers.databases.inputoutput import (
    useeio,
    exiobase
)
from greengraph.importers.databases.generic import graph_system_from_input_output_matrices

path_useeio_fixture = resources.files('tests.fixtures.databases').joinpath('fixture_USEEIOv2.0.1-411.xlsx')
path_exiobase_fixture = resources.files('tests.fixtures.databases').joinpath('fixture_IOT_2014_pxp.zip')


def test_format_useeio_matrices():
    try:
        dict_useeio = useeio.format_useeio_matrices(path_useeio=path_useeio_fixture)
        return dict_useeio
    except:
        raise Exception("Error in formatting USEEIO matrices")
    

def test_format_exiobase_matrices():
    try:
        dict_exiobase_files  = exiobase.unpack_exiobase_zip(path_zip=path_exiobase_fixture)
        dict_exiobase = exiobase.format_exiobase_matrices(
            path_A=dict_exiobase_files['path_A'],
            path_S=dict_exiobase_files['path_S'],
            path_S_metadata=dict_exiobase_files['path_S_metadata'],
        )
        return dict_exiobase
    except:
        raise Exception("Error in formatting USEEIO matrices")
    

def test_useeio_matrices_to_graph():
    try:
        dict_useeio = test_format_useeio_matrices()
        G = graph_system_from_input_output_matrices(
            name_system='useeio',
            assign_new_uuids=True,
            str_extension_nodes_uuid='name',
            str_production_nodes_uuid='name',
            str_indicator_nodes_uuid='name',
            matrix_convention='I-A',
            array_production=dict_useeio['A'].to_numpy(),
            array_extension=dict_useeio['B'].to_numpy(),
            array_indicator=dict_useeio['C'].to_numpy(),
            list_dicts_production_node_metadata=dict_useeio['dicts_A_metadata'],
            list_dicts_extension_node_metadata=dict_useeio['dicts_B_metadata'],
            list_dicts_indicator_node_metadata=dict_useeio['dicts_C_metadata'],
        )
        nodes_production = [n for n in G.nodes(data=True) if n[1]['type'] == 'production']
        nodes_extension = [n for n in G.nodes(data=True) if n[1]['type'] == 'extension']
        nodes_indicator = [n for n in G.nodes(data=True) if n[1]['type'] == 'indicator']

        number_of_edges_A = np.count_nonzero(dict_useeio['A'].to_numpy())
        number_of_edges_B = np.count_nonzero(dict_useeio['B'].to_numpy())
        number_of_edges_C = np.count_nonzero(dict_useeio['C'].to_numpy())
        assert len(G.edges()) == number_of_edges_A + number_of_edges_B + number_of_edges_C

        assert set(
            [data['name'] for uuid, data in nodes_production]
        ) == set([
            'Fresh soybeans, canola, flaxseeds, and other oilseeds',
            'Fresh wheat, corn, rice, and other grains',
            'Fresh vegetables, melons, and potatoes',
            'Fresh fruits and tree nuts'
        ])

        assert set(
            [data['name'] for uuid, data in nodes_extension]
        ) == set([
            '(1S)-Abscisic acid',
            '(1S)-Abscisic acid',
            '(1S)-Abscisic acid',
            '(E)-8-Dodecen-1-yl acetate'
        ])

        assert set(
            [data['name'] for uuid, data in nodes_indicator]
        ) == set([
            'Acidification Potential',
            'Commercial Construction and Demolition Debris',
            'Commercial Municipal Solid Waste',
            'Commercial RCRA Hazardous Waste'
        ])

        return G
    except:
        raise Exception("Error in converting USEEIO matrices to graph")