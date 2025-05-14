from greengraph.core import GreenMultiDiGraph
import numpy as np
import networkx as nx

data = np.array([
    [0, 1, 0],
    [1, 0, 5],
    [0, 0, 0]
])

nodelist = (
    ('N1', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
    ('N2', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
    ('N3', {'type': 'production', 'unit': 'kg', 'production': 1.0})
)

G = graph_from_matrix(
    matrix=data,
    nodes_axis_0=nodelist,
    nodes_axis_1=None,
    common_attributes_nodes_axis_0=None,
    common_attributes_nodes_axis_1=None,
    name_amount_attribute='amount',
    common_attributes_edges={'type': 'flow', 'unit': 'kg'},
    create_using=GreenMultiDiGraph,
)
# %%
