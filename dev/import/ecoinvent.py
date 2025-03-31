# %%
import bw2io as bi
from fsspec.implementations.zip import ZipFileSystem
from bw_processing import load_datapackage
import numpy as np
import networkx as nx
import xarray as xr

"""

eidp = load_datapackage(ZipFileSystem("/Users/michaelweinold/Downloads/ecoinvent-310-cutoff.83f3565f.zip"))

from matrix_utils import MappedMatrix

mmt = MappedMatrix(packages=[eidp], matrix="technosphere_matrix")

mmb = MappedMatrix(packages=[eidp], matrix="biosphere_matrix")

"""
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

matrix_technosphere = np.array(
    [
        [0.0, 0.0, 0.0],
        [1.3, 0.0, 0.0],
        [0.1, 0.2, 0.0]
    ]
)
indices_technosphere = [1, 2, 3]
metadata_technosphere = {
    1: {
        "name": "process one",
        "functional unit": "output one",
        "location": "CH",
        "type": "process",
        "sphere": "technosphere",
    },
    2: {
        "name": "process two",
        "functional unit": "output two",
        "location": "CH",
        "type": "process",
        "sphere": "technosphere",
    },
    3: {
        "name": "process three",
        "functional unit": "output three",
        "location": "CH",
        "type": "process",
        "sphere": "technosphere",
    },
}

matrix_biosphere = np.array(
    [
        [9.2, 0.0, 0.0],
        [0.0, 2.0, 3.3],
    ]
)
indices_biosphere = ['alpha', 'beta']
metadata_biosphere = {
    'alpha': {
        "name": "flow alpha",
        "unit": "kg",
        "type": "emission",
        "sphere": "biosphere",
    },
    'beta': {
        "name": "flow beta",
        "unit": "m^3",
        "type": "emission",
        "sphere": "biosphere",
    },
}

# Create graph
graph = nx.from_numpy_array(
    matrix_technosphere,
    create_using=nx.DiGraph,
    nodelist=indices_technosphere,
)
nx.set_node_attributes(graph, metadata_technosphere)  # Remove 'name' to flatten attributes

# Add biosphere nodes
graph.add_nodes_from(indices_biosphere)
nx.set_node_attributes(graph, metadata_biosphere)  # Remove 'name' to flatten attributes

# Add edges from biosphere matrix
edges = []
for i, source in enumerate(indices_biosphere):
    for j, target in enumerate(indices_technosphere):
        weight = matrix_biosphere[i, j]
        if weight != 0:
            edges.append((source, target, {'weight': weight}))

graph.add_edges_from(edges)

biosphere_nodes = [node for node, attrs in graph.nodes(data=True) if attrs['sphere'] == 'biosphere']
technosphere_nodes = [node for node, attrs in graph.nodes(data=True) if attrs['sphere'] == 'technosphere']

biadj_matrix = nx.bipartite.biadjacency_matrix(
    graph,
    row_order=biosphere_nodes,  # Rows: alpha, beta
    column_order=technosphere_nodes,  # Columns: 1, 2, 3
    weight='weight'
)

# Convert to dense array
biadj_array = biadj_matrix.toarray()

# Prepare metadata coordinates
biosphere_names = [metadata_biosphere[node]['name'] for node in biosphere_nodes]
biosphere_units = [metadata_biosphere[node]['unit'] for node in biosphere_nodes]
biosphere_types = [metadata_biosphere[node]['type'] for node in biosphere_nodes]
biosphere_spheres = [metadata_biosphere[node]['sphere'] for node in biosphere_nodes]

technosphere_names = [metadata_technosphere[node]['name'] for node in technosphere_nodes]
technosphere_functional_units = [metadata_technosphere[node]['functional unit'] for node in technosphere_nodes]
technosphere_locations = [metadata_technosphere[node]['location'] for node in technosphere_nodes]
technosphere_types = [metadata_technosphere[node]['type'] for node in technosphere_nodes]
technosphere_spheres = [metadata_technosphere[node]['sphere'] for node in technosphere_nodes]

# Create Xarray DataArray
ds = xr.DataArray(
    biadj_array,
    dims=['biosphere_node', 'technosphere_node'],
    coords={
        'biosphere_node': biosphere_nodes,
        'technosphere_node': technosphere_nodes,
        'biosphere_name': ('biosphere_node', biosphere_names),
        'biosphere_unit': ('biosphere_node', biosphere_units),
        'biosphere_type': ('biosphere_node', biosphere_types),
        'biosphere_sphere': ('biosphere_node', biosphere_spheres),
        'technosphere_name': ('technosphere_node', technosphere_names),
        'technosphere_functional_unit': ('technosphere_node', technosphere_functional_units),
        'technosphere_location': ('technosphere_node', technosphere_locations),
        'technosphere_type': ('technosphere_node', technosphere_types),
        'technosphere_sphere': ('technosphere_node', technosphere_spheres),
    }
)

# The result is in ds
print(ds)