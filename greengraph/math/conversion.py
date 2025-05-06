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
        lambdafunction_sort_keys = lambda node: tuple(G.nodes[node].get(key, None) for key in sort_keys)
        list_sorted_uuids_A = sorted(
            [node for node, attr in G.nodes(data=True) if attr('type') == 'production'],
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
                [node for node, attr in G.nodes(data=True) if attr('type') == 'biosphere'],
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
                [node for node, attr in G.nodes(data=True) if attr('type') == 'biosphere'],
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