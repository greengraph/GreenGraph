
# %%

import networkx as nx
import pandas as pd
import datashader as ds
import datashader.transfer_functions as tf
import datashader.layout as ds_layout
import datashader.bundling as ds_bundling
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd

import datashader as ds
import datashader.transfer_functions as tf
from datashader.layout import random_layout, circular_layout, forceatlas2_layout
from datashader.bundling import connect_edges, hammer_bundle


actual_selected_nodes = [node for node, attr in G.nodes(data=True) if attr['type'] == 'production']
GG = G.subgraph(actual_selected_nodes)

node_identifiers = list(G.nodes())
nodes = pd.DataFrame({'uuid': node_identifiers})

if not nodes.empty:
    node_to_int_index = {uuid: index for index, uuid in enumerate(nodes['uuid'])}
else:
    node_to_int_index = {}

edges_data = []
for u, v, data in GG.edges(data=True):
    source_idx = node_to_int_index.get(u)
    target_idx = node_to_int_index.get(v)
    edge_amount = data.get('flow')
    
    if source_idx is not None and target_idx is not None:
        edges_data.append({
            'source': source_idx,
            'target': target_idx,
            'amount': edge_amount
        })

edges = pd.DataFrame(edges_data)

# %%

circular  = circular_layout(nodes, uniform=False)
randomloc = random_layout(nodes)

cvsopts = dict(plot_height=1000, plot_width=1000)

def nodesplot(nodes, name=None, canvas=None, cat=None):
    canvas = ds.Canvas(**cvsopts) if canvas is None else canvas
    aggregator=None if cat is None else ds.count_cat(cat)
    agg=canvas.points(nodes,'x','y',aggregator)
    return tf.spread(tf.shade(agg, cmap=["#FF3333"]), px=3, name=name)

tf.Images(nodesplot(randomloc,"Random layout"),
          nodesplot(circular, "Circular layout"))

forcedirected = forceatlas2_layout(nodes, edges)

def edgesplot(edges, name=None, canvas=None):
    canvas = ds.Canvas(**cvsopts) if canvas is None else canvas
    return tf.shade(canvas.line(edges, 'x','y', agg=ds.count()), name=name)

def graphplot(nodes, edges, name="", canvas=None, cat=None):
    if canvas is None:
        xr = nodes.x.min(), nodes.x.max()
        yr = nodes.y.min(), nodes.y.max()
        canvas = ds.Canvas(x_range=xr, y_range=yr, **cvsopts)

    np = nodesplot(nodes, name + " nodes", canvas, cat)
    ep = edgesplot(edges, name + " edges", canvas)
    return tf.stack(ep, np, how="over", name=name)

cd = circular
fd = forcedirected

cd_d = graphplot(cd, connect_edges(cd,edges), "Circular layout")
fd_d = graphplot(fd, connect_edges(fd,edges), "Force-directed")
#cd_b = graphplot(cd, hammer_bundle(cd,edges), "Circular layout, bundled")
#fd_b = graphplot(fd, hammer_bundle(fd,edges), "Force-directed, bundled")

tf.Images(cd_d,fd_d).cols(2)

# %%

import networkx as nx
import pickle
import itertools

def ng(graph,name):
    graph.name = name
    return graph

def nx_layout(graph):
    layout = nx.circular_layout(graph)
    data = [[node] + layout[node].tolist() for node in graph.nodes]

    nodes = pd.DataFrame(data, columns=['id', 'x', 'y'])
    nodes.set_index('id', inplace=True)

    # --- MODIFIED LINE HERE ---
    # Assuming graph.edges is yielding (u, v, some_third_item)
    # Extract only the first two elements (u, v) for the DataFrame
    edge_node_pairs = [(u, v) for u, v, *_ in graph.edges(data=True, keys=True)]
    # The data=True, keys=True ensures we are iterating over what might provide extra items.
    # Using (u, v, *_) will take the first two items and ignore any further items (like data dict or key).
    # If you are certain it's always 3 items, (u, v, _) would also work.
    # A simpler and often more correct way if you ONLY want u,v pairs from any graph:
    # edge_node_pairs = list(graph.edges(data=False, keys=False))

    edges = pd.DataFrame(edge_node_pairs, columns=['source', 'target'])
    # --- END OF MODIFICATION ---

    return nodes, edges

def nx_plot(graph, name=""):
    print(graph.name, len(graph.edges))
    nodes, edges = nx_layout(graph)

    direct = connect_edges(nodes, edges)
    bundled_bw005 = hammer_bundle(nodes, edges)
    bundled_bw030 = hammer_bundle(nodes, edges, initial_bandwidth=0.30)

    return [graphplot(nodes, direct,         graph.name),
            graphplot(nodes, bundled_bw005, "Bundled bw=0.05"),
            graphplot(nodes, bundled_bw030, "Bundled bw=0.30")]


out = nx_plot(GG)
tf.Images(*chain.from_iterable([out])).cols(3)

# %%



# %%


paths_iterator = nx.shortest_simple_paths(
    G=GG,  # Assuming GGG was a typo and should be GG
    source='533b15e6-3d08-4939-844c-4722282dd1cd',
    target='4738082a-9137-4716-b666-aca9488a9657',
    weight='flow'
)
first_ten_paths = list(itertools.islice(paths_iterator, 10))
for path in first_ten_paths:

# %%

import pickle


with open('graph.pkl', 'wb') as f:
    pickle.dump(G, f)

# Example of loading the graph (optional, for completeness)
# with open('graph.pkl', 'rb') as f:
#     loaded_GG = pickle.load(f)
# print(f"Loaded graph has {loaded_GG.number_of_nodes()} nodes and {loaded_GG.number_of_edges()} edges.")
