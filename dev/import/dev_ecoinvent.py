# based on
# https://github.com/cmutel/spatial-assessment-blog/blob/master/notebooks/How%20to%20use%20ecoinvent.ipynb

# %%
from pathlib import Path
import networkx as nx
from greengraph.importers.databases.ecoinvent import ecoinvent


ecospold_xml_files = ecoinvent._extract_ecospold_xml_files(
    path=Path('/Users/michaelweinold/data/ecoinvent 3.10.1_cutoff_ecoSpold02'),
)

# %%

ecoinvent_node_and_edge_data = ecoinvent._prepare_ecoinvent_node_and_edge_lists(
    process_nodes=ecospold_xml_files['process_nodes'],
    product_nodes=ecospold_xml_files['product_nodes'],
    ecosphere_flows_mapping=ecospold_xml_files['ecosphere_flows_mapping'],
    technosphere_edges=ecospold_xml_files['technosphere_edges'],
    ecosphere_edges=ecospold_xml_files['ecosphere_edges'],
)


# %%

from greengraph.importers.databases.generic import graph_system_from_node_and_edge_lists

G = graph_system_from_node_and_edge_lists(
    name_system="ecoinvent 3.10",
    assign_new_uuids=True,
    str_production_nodes_uuid="brightway_code_process",
    str_extension_nodes_uuid="brightway_code_extension",
    list_dicts_production_nodes_metadata=ecoinvent_node_and_edge_data['nodes_production'],
    list_dicts_extension_nodes_metadata=ecoinvent_node_and_edge_data['nodes_extension'],
    list_tuples_production_edges=ecoinvent_node_and_edge_data['edges_production'],
    list_tuples_extension_edges=ecoinvent_node_and_edge_data['edges_extension'],
)


# %%


import pickle
with open('/Users/michaelweinold/github/GreenGraph/dev/Geco.pkl', 'wb') as f:
    pickle.dump(G, f)

# %%

M = G.generate_matrices(
    matrixformat='csr',
    generate_A=True,
    generate_B=True,
    generate_Q=False,
)
# %%

M.lca(
    demand={G.get_random_node(type='production'): 1.0},
    format_return='xarray',
)
