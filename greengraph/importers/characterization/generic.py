# %%
import uuid
import networkx as nx
import xarray as xr
import pandas as pd
import numpy as np
import greengraph.importers
import greengraph.importers.characterization
import greengraph.importers.characterization.impact_world_plus
from greengraph.utility.logging import logtimer
import greengraph
from greengraph.utility.data import create_dynamic_lookup_dictionary
import logging
from greengraph.utility.graph import from_biadjacency_matrix

Q = greengraph.importers.characterization.impact_world_plus.generate_iwp_characterization_matrix_exiobase(
    type_iwp='expert_version',
    version_iwp='2.1',
)

def add_characterization_to_graph(
    name_method: str,
    G: nx.MultiDiGraph,
    matrix_characterization: np.ndarray,
    list_dicts_characterization_node_metadata: list[dict],
    list_dicts_biosphere_node_metadata: list[dict],
) -> None:
    
    for idx, dict_impactcategory_metadata in enumerate(list_dicts_characterization_node_metadata):
        dict_impactcategory_metadata['uuid'] = str(uuid.uuid4())
        dict_impactcategory_metadata['index'] = idx
        dict_impactcategory_metadata['method'] = name_method

    for dict_biosphere_node in list_dicts_biosphere_node_metadata:
        name = dict_biosphere_node["name"]
        for node, attrs in G.nodes(data=True):
            if attrs.get("name") == name:
                dict_biosphere_node["uuid"] = node
                break
        else:
            dict_biosphere_node["uuid"] = "No match found in graph!"

    matrix_characterization = xr.DataArray(
        matrix_characterization,
        dims=['rows', 'cols'],
        coords={
            'rows': [node_metadata['uuid'] for node_metadata in list_dicts_characterization_node_metadata],
            'cols': [node_metadata['uuid'] for node_metadata in list_dicts_biosphere_node_metadata]
        }
    )

    return matrix_characterization


def add_characterization_to_graph_from_matrix(
    G: nx.MultiDiGraph,
    array_characterization: np.ndarray,
    list_dicts_characterization_node_metadata: list[dict],
    list_dicts_extension_node_metadata: list[dict],
) -> None:
    
    for node in list_dicts_characterization_node_metadata:
        node['uuid'] = str(uuid.uuid4())
    
    dict_extension_node_uuid_lookup = create_dynamic_lookup_dictionary(
        list_dicts=[
            {**attr, 'uuid': node}
            for node, attr in G.nodes(data=True)
            if attr.get('type') == 'extension'
        ],
        list_key_fields=['name'],
        value_field='uuid'
    )

    for node in list_dicts_extension_node_metadata:
        node['uuid'] = dict_extension_node_uuid_lookup.get(node['name'])
    
    matrix_characterization = xr.DataArray(
        matrix_characterization,
        dims=['rows', 'cols'],
        coords={
            'rows': [node_metadata['uuid'] for node_metadata in list_dicts_characterization_node_metadata],
            'cols': [node_metadata['uuid'] for node_metadata in list_dicts_extension_node_metadata]
        }
    )

    with logtimer("creating MultiDiGraph from characterization matrix."):
        Q = from_biadjacency_matrix(
            matrix=matrix_characterization.values,
            nodes_axis_0=matrix_characterization.coords['rows'].values.tolist(),
            nodes_axis_1=matrix_characterization.coords['cols'].values.tolist(),
            attributes_nodes_axis_0={'type': 'characterization'},
            attributes_nodes_axis_1={'type': 'extension'},
            create_using=nx.MultiDiGraph
        )