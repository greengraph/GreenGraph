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
    technosphere_sorted_uuids = sorted(
        [node for node in G.nodes() if G.nodes[node].get('type') == 'technosphere'],
        key=lambda node: tuple(G.nodes[node][attr] for attr in technosphere_matrix_sorting_attributes)
    )
    biosphere_sorted_uuids = sorted(
        [node for node in G.nodes() if G.nodes[node].get('type') == 'biosphere'],
        key=lambda node: tuple(G.nodes[node][attr] for attr in biosphere_matrix_sorting_attributes)
    )
    with logtimer("Generating technosphere matrix."):
        A = nx.algorithms.bipartite.biadjacency_matrix(
            G,
            row_order=technosphere_sorted_uuids,
            column_order=technosphere_sorted_uuids,
            dtype=float,
            weight='flow',
            format='dense'
        )
        A = xr.DataArray(
            A,
            dims=('rows', 'cols'),
            coords={
                'rows': technosphere_sorted_uuids,
                'cols': technosphere_sorted_uuids,
            },
        )
    with logtimer("Generating biosphere matrix."):
        B = nx.algorithms.bipartite.biadjacency_matrix(
            G,
            row_order=biosphere_sorted_uuids,
            column_order=technosphere_sorted_uuids,
            dtype=float,
            weight='flow',
            format='dense'
        )
        B = xr.DataArray(
            B,
            dims=('rows', 'cols'),
            coords={
                'rows': biosphere_sorted_uuids,
                'cols': technosphere_sorted_uuids,
            },
        )

    with logtimer("Normalizing technosphere matrix ('I-A'-convention)."):
        array_production = np.array([G.nodes[node]['production'] for node in A.coords['rows'].values])
        Anorm = A / array_production
        Bnorm = B / array_production
    if dense:
        pass
    else:
        #TODO how to combine xarray and sparse matrices?
        #Anorm = Anorm.tocsr()
        #Bnorm = Bnorm.tocsr()
        pass
    
    return Anorm, Bnorm