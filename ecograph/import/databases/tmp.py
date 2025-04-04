import networkx as nx
import numpy as np
import rustworkx as rx

# %%

T1 = np.array([[0.15, 0.25, 0.11],
              [0.20, 0.05, 0.54],
              [0.65, 0.70, 0.35]])

GT1 = rx.PyDiGraph.from_adjacency_matrix(T1)

T1_node_data = {
    0: {"name": 'proc1'},
    1: {"name": 'proc2'},
    2: {"name": 'proc3'},
}

for i in range(T1.shape[0]):
    GT1[i] = T1_node_data[i]

T2 = np.array([[0.15, 0.25, 0.11],
              [0.0, 0.05, 0.54]])