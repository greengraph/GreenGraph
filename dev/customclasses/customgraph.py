# %%
from greengraph.core import GreenGraphMultiDiGraph
import numpy as np
import networkx as nx

data = np.array([
    [0, 1, 0],
    [1, 0, 5],
    [0, 0, 0]
])

dt = [('amount', float), ('type', 'U10')]
A = np.zeros(data.shape, dtype=dt)
A['amount'] = data.astype(float)
A['type'] = 'flow'

nodelist = (
    ('N1', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
    ('N2', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
    ('N3', {'type': 'production', 'unit': 'kg', 'production': 1.0})
)
nodelist_simple = [node for node, attrs in nodelist]

custom_graph = nx.from_numpy_array(
    data,
    nodelist=nodelist_simple,
    create_using=GreenGraphMultiDiGraph,
)