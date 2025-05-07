# %%
from greengraph.utility.logging import logtimer
import networkx as nx
import numpy as np
import xarray as xr


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
            lambdafunction_sort_keys = lambda node: tuple(G.nodes[node].get(key, None) for key in sort_keys)
        list_sorted_uuids_B = sorted(
            [node for node, attr in G.nodes(data=True) if attr['type'] == 'extension'],
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
            lambdafunction_sort_keys = lambda node: tuple(G.nodes[node].get(key, None) for key in sort_keys)
        list_sorted_uuids_Q = sorted(
            [node for node, attr in G.nodes(data=True) if attr['type'] == 'indicator'],
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

# %%

from greengraph.importers.databases.inputoutput import useeio
from greengraph.importers.databases.generic import graph_system_from_input_output_matrices
dct = useeio.load_useeio_data_from_zenodo(version='2.0.1-411')
G = graph_system_from_input_output_matrices(
    name_system='useeio',
    assign_new_uuids=True,
    str_extension_nodes_uuid='name',
    str_production_nodes_uuid='name',
    str_indicator_nodes_uuid='name',
    matrix_convention='I-A',
    array_production=dct['A'].to_numpy(),
    array_extension=dct['B'].to_numpy(),
    array_indicator=dct['C'].to_numpy(),
    list_dicts_production_node_metadata=dct['dicts_A_metadata'],
    list_dicts_extension_node_metadata=dct['dicts_B_metadata'],
    list_dicts_indicator_node_metadata=dct['dicts_C_metadata'],
)

# %%

matrices = _generate_matrices_from_graph(
    G=G,
    matrixformat='dense',
    A=True,
    B=True,
    Q=True,
    A_sort_attributes=None,
    B_sort_attributes=None,
    Q_sort_attributes=None
)
