# %%
from ecograph.utility.logging import logtimer
import networkx as nx
import numpy as np
import xarray as xr


def _generate_matrices_from_graph(
    G: nx.MultiDiGraph,
    technosphere_matrix_sorting_attributes: list[str] = None,
    biosphere_matrix_sorting_attributes: list[str] = None,
    dense: bool = False,
) -> np.ndarray:
    """
    Generate matrices.......
    """
    technosphere_row_and_column_order = sorted(
        [node for node in G.nodes() if G.nodes[node].get('type') == 'technosphere'],
        key=lambda node: tuple(G.nodes[node][attr] for attr in technosphere_matrix_sorting_attributes)
    )
    biosphere_row_order = sorted(
        [node for node in G.nodes() if G.nodes[node].get('type') == 'biosphere'],
        key=lambda node: tuple(G.nodes[node][attr] for attr in biosphere_matrix_sorting_attributes)
    )
    with logtimer("Generating technosphere matrix."):
        A = nx.algorithms.bipartite.biadjacency_matrix(
            G,
            row_order=technosphere_row_and_column_order,
            column_order=technosphere_row_and_column_order,
            dtype=float,
            weight='flow',
            format='csr'
        )
    with logtimer("Generating biosphere matrix."):
        B = nx.algorithms.bipartite.biadjacency_matrix(
            G,
            row_order=biosphere_row_order,
            column_order=technosphere_row_and_column_order,
            dtype=float,
            weight='flow',
            format='csr'
        )
    with logtimer("Normalizing technosphere matrix ('I-A'-convention)."):
        A = A.todense()
        B = B.todense()
        array_production = np.array([G.nodes[node]['production'] for node in list(G.nodes())])
        Anorm = A / array_production
        Bnorm = B / array_production
    if dense:
        pass
    else:
        Anorm = Anorm.tocsr()
        Bnorm = Bnorm.tocsr()
    
    Anorm = xr.DataArray(
        Anorm,
        dims=('rows', 'cols'),
        coords={
            'rows': technosphere_row_and_column_order,
            'cols': technosphere_row_and_column_order,
        },
    )
    Bnorm = xr.DataArray(
        Bnorm,
        dims=('rows', 'cols'),
        coords={
            'rows': biosphere_row_order,
            'cols': technosphere_row_and_column_order,
        },
    )
        
    return Anorm, Bnorm