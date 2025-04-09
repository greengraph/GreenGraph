# %%
from ecograph.utility.logging import logtimer
import networkx as nx
import numpy as np

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
    with logtimer("Converting from sparse to dense matrices."):
        A = A.todense()
        B = B.todense()
    return A, B
