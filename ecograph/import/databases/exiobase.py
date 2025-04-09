# %%
import networkx as nx
import pandas as pd
import numpy as np
import scipy as sp
import logging
from pathlib import Path
import uuid

path_A = '/Users/michaelweinold/data/IOT_2022_ixi/A.txt'
path_S = '/Users/michaelweinold/data/IOT_2022_ixi/satellite/S.txt'
path_U = '/Users/michaelweinold/data/IOT_2022_ixi/satellite/unit.txt'
path_exiobase_root = '/Users/michaelweinold/data/IOT_2022_ixi'

data_technology_matrix = pd.read_csv(
    path_exiobase_root + '/A.txt',
    delimiter='\t',
    skiprows=3,
    header=None
)

number_of_sectors = data_technology_matrix.shape[0]

sector_metadata = data_technology_matrix.iloc[:, [0, 1]].copy()
sector_metadata.columns = ['location', 'name']
sector_metadata['index'] = range(number_of_sectors)
sector_metadata['uuid'] = [str(uuid.uuid4()) for _ in range(number_of_sectors)]

G = nx.from_numpy_array(
    data_technology_matrix.iloc[:, 2:].to_numpy(),
    create_using=nx.DiGraph,
    parallel_edges=False,
    edge_attr='weight',
    nodelist=sector_metadata['uuid'].tolist(),
)

technology_matrix_graph_attributes = {}
for idx, row in sector_metadata.iterrows():
    technology_matrix_graph_attributes[row['uuid']] = {
        'name': row['name'],
        'type': 'technosphere',
        'system': 'exiobase',
        'unit': 'USD',
        'index': row['index']
    }
nx.set_node_attributes(G, technology_matrix_graph_attributes)

# %%

data_satellite_matrix = pd.read_csv(
    path_exiobase_root + '/satellite/S.txt',
    delimiter='\t',
    skiprows=3,
    header=None
)

satellite_metadata = pd.read_csv(
    path_exiobase_root + '/satellite/unit.txt',
    delimiter='\t',
    skiprows=1,
    header=None
)
number_of_satellites = data_satellite_matrix.shape[0]
satellite_metadata.columns = ['satellite', 'unit']
satellite_metadata['index'] = range(number_of_satellites)
satellite_metadata['uuid'] = [str(uuid.uuid4()) for _ in range(number_of_satellites)]


B = nx.algorithms.bipartite.from_biadjacency_matrix(
    sp.sparse.csr_matrix(data_satellite_matrix.iloc[:, 1:]),
    create_using=nx.DiGraph,
    edge_attribute='flow',
)


satellite_uuid_mapping = {idx: row['uuid'] for idx, row in satellite_metadata.iterrows()}
sector_uuid_mapping = {idx + len(satellite_metadata): row['uuid'] for idx, row in sector_metadata.iterrows()}
combined_uuid_mapping = satellite_uuid_mapping | sector_uuid_mapping


nx.relabel_nodes(B, combined_uuid_mapping, copy=False)

# %%

satellite_matrix_graph_attributes = {}
for idx, row in satellite_metadata.iterrows():
    satellite_matrix_graph_attributes[row['uuid']] = {
        'name': row['satellite'],
        'type': 'biosphere',
        'system': 'exiobase',
        'unit': row['unit'],
        'index': row['index']
    }

for node in B.nodes():
    B.nodes[node].clear()
nx.set_node_attributes(B, satellite_matrix_graph_attributes)

# %%
# merging graphs

M = nx.compose(B, G)

nx.algorithms.bipartite.biadjacency_matrix(
    M,
    row_order = [n for n in M.nodes() if M.nodes[n]['type'] == 'biosphere'],
    column_order = [n for n in M.nodes() if M.nodes[n]['type'] == 'technosphere'],
    weight='flow',
).todense()

labeled_array.sel(rows=[n for n in M.nodes() if M.nodes[n]['type'] == 'biosphere'][5], cols=[n for n in M.nodes() if M.nodes[n]['type'] == 'technosphere'][7]).values

labeled_array = xr.DataArray(
    arrB, 
    dims=['rows', 'cols'], 
    coords={'rows': [n for n in M.nodes() if M.nodes[n]['type'] == 'biosphere'], 'cols': [n for n in M.nodes() if M.nodes[n]['type'] == 'technosphere']}
)

# %%
# exporting the relevant matrices to xarrays
