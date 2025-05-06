# %%

import pandas as pd
from pathlib import Path
import uuid
from greengraph.utility.logging import logtimer
import networkx as nx

path = Path('/Users/michaelweinold/data/ecoinvent 3.11_LCIA_implementation/LCIA Implementation 3.11.xlsx')
# 3.10 file takes forever to merge...whyever?!
path_310 = Path('/Users/michaelweinold/Downloads/ecoinvent 3.10_LCIA_implementation/LCIA Implementation 3.10.xlsx')

def load_ecoinvent_characterization_data(
    path: Path,
    version: str,
) -> list:
    r"""

    Warnings
    --------
    In the `ecoinvent 3.10_LCIA_implementation` Excel file, sheet `Indicators`,
    rows are heavily duplicated. It is necessary to drop duplicates
    before merging with the `CFs` sheet. This is not the case in the
    `ecoinvent 3.11_LCIA_implementation` Excel file.
    """
    _versions_name_units = {
        "3.11": "CFs",
        "3.10": "CFs",
    }
    if version not in _versions_name_units:
        raise ValueError(
            f"Version {version} not supported. Supported versions are: {_versions_name_units.keys()}"
        )

    with logtimer('reading Ecoinvent characterization data from Excel file.'):
        df_cf_edges = pd.read_excel(
            path,
            sheet_name="CFs",
            header=0
        ).drop_duplicates()
        df_units = pd.read_excel(
            path,
            sheet_name="Indicators",
            header=0
        ).drop_duplicates()
    
    with logtimer('preparing Ecoinvent characterization data.'):
        df_cf_edges_with_units = pd.merge(
            df_cf_edges,
            df_units,
            on=['Method', 'Category', 'Indicator'],
            how="left"
        )
        df_cf_edges_with_units.columns = df_cf_edges_with_units.columns.str.lower()

        df_cf = df_cf_edges_with_units[['method', 'category', 'indicator', 'indicator unit']].drop_duplicates()
        df_cf['uuid_charcterization'] = [str(uuid.uuid4()) for _ in range(len(df_cf))]
        df_cf['unit'] = df_cf['indicator unit']

        df_cf_edges_with_units = df_cf_edges_with_units.merge(
            df_cf,
            on=['method', 'category', 'indicator'],
            how="left",
        )
    
    dict_cf_edges = list(
        zip(
            df_cf_edges_with_units[['name', 'compartment', 'subcompartment']].to_dict(orient='records'),
            df_cf_edges_with_units[['method', 'category', 'indicator', 'unit']].to_dict(orient='records'),
            df_cf_edges_with_units['cf'],
        )
    )

    return dict_cf_edges

out = load_ecoinvent_characterization_data(path=path, version='3.11')


# %%

from pathlib import Path
import networkx as nx
from greengraph.importers.databases.ecoinvent import _prepare_ecoinvent_node_and_edge_lists

from greengraph.importers.databases.ecoinvent import (
    _extract_ecospold_xml_files,
    _prepare_ecoinvent_node_and_edge_lists,
)

ecospold_xml_files = _extract_ecospold_xml_files(
    path=Path('/Users/michaelweinold/data/ecoinvent 3.7.1_apos_ecoSpold02'),
)

# %%

ecoinvent_node_and_edge_data = _prepare_ecoinvent_node_and_edge_lists(
    process_nodes=ecospold_xml_files['process_nodes'],
    product_nodes=ecospold_xml_files['product_nodes'],
    ecosphere_flows_mapping=ecospold_xml_files['ecosphere_flows_mapping'],
    technosphere_edges=ecospold_xml_files['technosphere_edges'],
    ecosphere_edges=ecospold_xml_files['ecosphere_edges'],
)

# %%

# %%

from greengraph.importers.databases.generic import graph_system_from_node_and_edge_lists


G = graph_system_from_node_and_edge_lists(
    name_system="ecoinvent 3.11",
    assign_new_uuids=True,
    str_production_nodes_uuid="brightway_code_process",
    str_extension_nodes_uuid="brightway_code_extension",
    list_dicts_production_nodes_metadata=ecoinvent_node_and_edge_data['nodes_production'],
    list_dicts_extension_nodes_metadata=ecoinvent_node_and_edge_data['nodes_extension'],
    list_tuples_production_edges=ecoinvent_node_and_edge_data['edges_production'],
    list_tuples_extension_edges=ecoinvent_node_and_edge_data['edges_biosphere'],
)

# %%

# %%

# %%

from greengraph.utility.data import (
    _create_dynamic_lookup_dictionary,
    _dict_to_tuple,
    _remove_duplicate_dictionaries
)

dict_lookup_extension_nodes = _create_dynamic_lookup_dictionary(G=G, node_type='extension', list_attributes=['name', 'compartment', 'subcompartment'])

list_nodes_char = _remove_duplicate_dictionaries([item[1] for item in out])
for node in list_nodes_char:
    node['type'] = 'characterization'
    node['uuid'] = str(uuid.uuid4())

GG = nx.MultiDiGraph()

GG.add_nodes_from(
    [
        (
            node['uuid'], 
            {key: value for key, value in node.items() if key != 'uuid'}
        )
        for node in list_nodes_char
    ]
)

dict_lookup_characterization_nodes = _create_dynamic_lookup_dictionary(
    G=GG,
    node_type='characterization',
    list_attributes=['method', 'category', 'indicator', 'unit']
)

list_uuids_ext = [dict_lookup_extension_nodes.get(_dict_to_tuple(item[0])) for item in out]
list_uuids_char = [dict_lookup_characterization_nodes.get(_dict_to_tuple(item[1])) for item in out]


GG.add_edges_from(
    list(zip(list_uuids_ext, list_uuids_char, [i[2] for i in out]))
)

# %%

import xarray as xr
import numpy as np

def _generate_matrices_from_graph(
    G: nx.MultiDiGraph,
    matrixformat: str,
    A: bool,
    B: bool,
    Q: bool,
    A_sort_attributes: list[str] = None,
    B_sort_attributes: list[str] = None,
    Q_sort_attributes: list[str] = None,
) -> np.ndarray:
    """
    Generate matrices.......
    """
    if A == False:
        raise ValueError("A must be True.")
    if B == False and Q == True:
        raise ValueError("B must be True if Q is True.")

    if A_sort_attributes is None:
        lambdafunction_sort_keys = lambda node: node
    else:
        lambdafunction_sort_keys = lambda node: tuple(G.nodes[node].get(key, None) for key in A_sort_attributes)
    list_sorted_uuids_A = sorted(
        [node for node, attr in G.nodes(data=True) if attr['type'] == 'production'],
        key=lambdafunction_sort_keys
    )

    with logtimer("Generating technosphere matrix."):
        A = nx.algorithms.bipartite.biadjacency_matrix(
            G,
            row_order=list_sorted_uuids_A,
            column_order=list_sorted_uuids_A,
            dtype=float,
            weight='flow',
            format=matrixformat
        )
        A = xr.DataArray(
            A,
            dims=('rows', 'cols'),
            coords={
                'rows': list_sorted_uuids_A,
                'cols': list_sorted_uuids_A,
            },
        )

    with logtimer("Normalizing technosphere matrix ('I-A'-convention)."):
        array_production = np.array([G.nodes[node]['production'] for node in A.coords['rows'].values])
        Anorm = A / array_production

    if B == True:
        if B_sort_attributes is None:
            lambdafunction_sort_keys = lambda node: node
        else:
            lambdafunction_sort_keys = lambda node: tuple(G.nodes[node].get(key, None) for key in B_sort_attributes)
        list_sorted_uuids_B = sorted(
            [node for node, attr in G.nodes(data=True) if attr['type'] == 'biosphere'],
            key=lambdafunction_sort_keys
        )

        with logtimer("Generating biosphere matrix."):
            B = nx.algorithms.bipartite.biadjacency_matrix(
                G,
                row_order=list_sorted_uuids_B,
                column_order=list_sorted_uuids_A,
                dtype=float,
                weight='flow',
                format='dense'
            )
            B = xr.DataArray(
                B,
                dims=('rows', 'cols'),
                coords={
                    'rows': list_sorted_uuids_B,
                    'cols': list_sorted_uuids_A,
                },
            )

        with logtimer("Normalizing biosphere matrix ('I-B'-convention)."):
            Bnorm = B / array_production

    if Q == True:
        if Q_sort_attributes is None:
            lambdafunction_sort_keys = lambda node: node
        else:
            lambdafunction_sort_keys = lambda node: tuple(G.nodes[node].get(key, None) for key in Q_sort_attributes)
        list_sorted_uuids_Q = sorted(
            [node for node, attr in G.nodes(data=True) if attr['type'] == 'biosphere'],
            key=lambdafunction_sort_keys
        )

        with logtimer("Generating characterization matrix."):
            Q = nx.algorithms.bipartite.biadjacency_matrix(
                G,
                row_order=list_sorted_uuids_Q,
                column_order=list_sorted_uuids_B,
                dtype=float,
                weight='flow',
                format='dense'
            )
            Q = xr.DataArray(
                Q,
                dims=('rows', 'cols'),
                coords={
                    'rows': list_sorted_uuids_Q,
                    'cols': list_sorted_uuids_B,
                },
            )

    return {
        'A': A,
        'Anorm': Anorm,
        'B': B,
        'Bnorm': Bnorm,
        'Q': Q
    }