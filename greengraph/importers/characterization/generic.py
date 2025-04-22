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