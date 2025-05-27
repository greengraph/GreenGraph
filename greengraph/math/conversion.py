# %%
from greengraph.utility.logging import logtimer
import networkx as nx
import numpy as np
import xarray as xr
from typing import Optional


def _generate_matrices_from_graph(
    G: nx.MultiDiGraph,
    matrixformat: str,
    generate_A: bool,
    generate_B: bool,
    generate_Q: bool,
    A_sort_attributes: Optional[list[str]] = None,
    B_sort_attributes: Optional[list[str]] = None,
    Q_sort_attributes: Optional[list[str]] = None,
) -> dict:
    """
    Generate matrices.......
    """
    if generate_A == False:
        raise ValueError("A must be True.")
    if generate_B == False and generate_Q == True:
        raise ValueError("B must be True if Q is True.")

    if A_sort_attributes is None:
        lambdafunction_sort_keys = lambda node: node
    else:
        lambdafunction_sort_keys = lambda node: tuple(G.nodes[node].get(key, None) for key in A_sort_attributes)
    list_sorted_uuids_A = sorted(
        [node for node, attr in G.nodes(data=True) if attr['type'] == 'production'],
        key=lambdafunction_sort_keys
    )

    with logtimer("Generating production matrix."):
        A = nx.algorithms.bipartite.biadjacency_matrix(
            G,
            row_order=list_sorted_uuids_A,
            column_order=list_sorted_uuids_A,
            dtype=float,
            weight='amount',
            format=matrixformat
        )
        A = xr.DataArray(
            A,
            dims=('production nodes (rows)', 'production nodes (cols)'),
            coords={
                'production nodes (rows)': list_sorted_uuids_A,
                'production nodes (cols)': list_sorted_uuids_A,
            },
        )

    with logtimer("Normalizing production matrix ('I-A'-convention)."):
        array_production = np.array([G.nodes[node]['production'] for node in A.coords['production nodes (rows)'].values])
        Anorm = A / array_production

    if generate_B == False:
        return {
        'A': A,
        'Anorm': Anorm,
        'B': None,
        'Bnorm': None,
        'Q': None
    }
    else:
        if B_sort_attributes is None:
            lambdafunction_sort_keys = lambda node: node
        else:
            lambdafunction_sort_keys = lambda node: tuple(G.nodes[node].get(key, None) for key in B_sort_attributes)
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
                weight='amount',
                format='dense'
            )
            B = xr.DataArray(
                B,
                dims=('extension nodes (rows)', 'production nodes (cols)'),
                coords={
                    'extension nodes (rows)': list_sorted_uuids_B,
                    'production nodes (cols)': list_sorted_uuids_A,
                },
            )

        with logtimer("Normalizing biosphere matrix ('I-B'-convention)."):
            Bnorm = B / array_production

    if generate_Q == False:
        return {
        'A': A,
        'Anorm': Anorm,
        'B': B,
        'Bnorm': Bnorm,
        'Q': None
    }
    else:
        if Q_sort_attributes is None:
            lambdafunction_sort_keys = lambda node: node
        else:
            lambdafunction_sort_keys = lambda node: tuple(G.nodes[node].get(key, None) for key in Q_sort_attributes)
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
                weight='weight',
                format='dense'
            )
            Q = xr.DataArray(
                Q,
                dims=('indicator nodes (rows)', 'extension nodes (cols)'),
                coords={
                    'indicator nodes (rows)': list_sorted_uuids_Q,
                    'extension nodes (cols)': list_sorted_uuids_B,
                },
            )

    return {
        'A': A,
        'Anorm': Anorm,
        'B': B,
        'Bnorm': Bnorm,
        'Q': Q
    }