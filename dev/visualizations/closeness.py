# %%

GG = G.subgraph([node for node, attr in G.nodes(data=True) if attr['type'] == 'production'])
import networkx as nx
import matplotlib.pyplot as plt
import random
import networkx as nx
import matplotlib.pyplot as plt
import random

# --- User-defined parameters ---
# For edge filtering and initial node selection
edge_attribute_name = 'flow' # e.g., 'weight'
threshold_value = 0.03      # e.g., 0.5
num_nodes_to_select = 40 

# For plot appearance
figure_width = 16
figure_height = 12
node_size_attribute = 'annual_production'
node_size_scaling_factor = 0.000000005 # Adjust this to make nodes bigger/smaller based on attribute
default_node_size_if_attribute_missing = 50 # Fallback size if 'annual_production' is not found
# -------------------------------


# IMPORTANT: Ensure your frozen graph GG is defined before this point.
# GG should have nodes with the 'annual_production' attribute if you want to use it for sizing.
# Example for testing (replace with your actual GG definition):
# GG = nx.complete_graph(25, create_using=nx.freeze)
# if GG is not None and isinstance(GG, nx.Graph):
#     temp_GG_for_attr = nx.Graph(GG) 
#     for node_id in temp_GG_for_attr.nodes(): # Add 'annual_production' for test
#         temp_GG_for_attr.nodes[node_id][node_size_attribute] = random.randint(100, 2000)
#     if edge_attribute_name != 'YOUR_ATTRIBUTE_NAME_HERE': # Add edge attributes for test
#         for u, v, data_dict in temp_GG_for_attr.edges(data=True):
#             data_dict[edge_attribute_name] = random.uniform(0.0, 2.0)
#     GG = nx.freeze(temp_GG_for_attr)
# else:
#     print("Error: GG is not defined for the test setup.")
#     exit()


if GG is None or not isinstance(GG, nx.Graph):
    print("Error: Your graph GG is not properly defined or is not a NetworkX graph.")
    print("Please ensure GG is a frozen NetworkX graph object before running this script.")
    exit()

if not nx.is_frozen(GG):
    print("Warning: The input graph GG was not frozen as expected from previous context.")
    print("A mutable copy will be made and used for modifications anyway.")


mutable_GG = nx.Graph(GG)
# If your original GG is a DiGraph, MultiGraph, or MultiDiGraph,
# you should use the corresponding constructor for the copy:
# mutable_GG = nx.DiGraph(GG)
# mutable_GG = nx.MultiGraph(GG)
# mutable_GG = nx.MultiDiGraph(GG)

edges_to_remove = []
if mutable_GG.number_of_edges() > 0:
    for u, v, attributes in mutable_GG.edges(data=True):
        attribute_val = attributes.get(edge_attribute_name)
        if attribute_val is not None:
            if attribute_val < threshold_value:
                edges_to_remove.append((u, v))
    
    original_edge_count_copy = mutable_GG.number_of_edges()
    mutable_GG.remove_edges_from(edges_to_remove)
    new_edge_count_copy = mutable_GG.number_of_edges()
    
    print(f"Original number of edges in the mutable copy: {original_edge_count_copy}")
    print(f"Removed {len(edges_to_remove)} edges from the mutable copy where '{edge_attribute_name}' < {threshold_value}.")
    print(f"Current number of edges in the mutable copy after removal: {new_edge_count_copy}")
else:
    print("Mutable copy of the graph initially had no edges.")


all_nodes_from_mutable = list(mutable_GG.nodes())
selected_nodes_list = []

if len(all_nodes_from_mutable) >= num_nodes_to_select:
    selected_nodes_list = random.sample(all_nodes_from_mutable, num_nodes_to_select)
    print(f"Selected {num_nodes_to_select} random nodes from the modified mutable graph:")
    print(selected_nodes_list)
elif len(all_nodes_from_mutable) > 0:
    selected_nodes_list = all_nodes_from_mutable
    print(f"Modified mutable graph has only {len(all_nodes_from_mutable)} nodes. Selecting all available nodes:")
    print(selected_nodes_list)
else:
    print("Modified mutable graph has no nodes from which to select random nodes.")


if not list(mutable_GG.nodes()):
    print("Graph mutable_GG has no nodes after processing. Cannot compute centrality or plot.")
else:
    closeness_centrality = nx.closeness_centrality(mutable_GG)
    
    node_list_for_plot = list(mutable_GG.nodes())
    
    closeness_values = [closeness_centrality.get(node, 0) for node in node_list_for_plot]

    # Prepare node sizes based on 'annual_production'
    node_sizes_by_attribute = []
    for node_id in node_list_for_plot:
        production_value = mutable_GG.nodes[node_id].get(node_size_attribute, 0) # Default to 0 if not found
        # Ensure production_value is a number, use default if not or if negative (size can't be negative)
        if not isinstance(production_value, (int, float)) or production_value < 0:
            node_size = default_node_size_if_attribute_missing
        else:
            node_size = production_value * node_size_scaling_factor
        # Add a minimum size to ensure nodes are visible even if production is very low/zero
        node_sizes_by_attribute.append(max(node_size, default_node_size_if_attribute_missing / 2 if production_value > 0 else default_node_size_if_attribute_missing))


    fig, ax = plt.subplots(figsize=(figure_width, figure_height)) # Use configurable plot size
    
    pos = None
    if len(node_list_for_plot) > 0 :
        if mutable_GG.number_of_edges() > 0 or len(node_list_for_plot) > 1 :
             pos = nx.spring_layout(mutable_GG, seed=42, k=0.5, iterations=50)
        elif len(node_list_for_plot) == 1:
             pos = {node_list_for_plot[0]: (0.5,0.5)}
    
    if pos is None and len(node_list_for_plot) > 0 :
        pos = nx.random_layout(mutable_GG, seed=42)
    elif pos is None and len(node_list_for_plot) == 0:
        pos = {}


    nodes_plot = nx.draw_networkx_nodes(
        mutable_GG,
        pos,
        ax=ax,
        nodelist=node_list_for_plot,
        node_color=closeness_values,
        cmap=plt.cm.viridis,
        node_size=node_sizes_by_attribute, # Use dynamic node sizes
        alpha=0.9
    )
    
    if mutable_GG.number_of_edges() > 0 and pos is not None:
        edgelist_no_loops = [(u,v) for u,v in mutable_GG.edges() if u!=v]
        nx.draw_networkx_edges(
            mutable_GG,
            pos,
            ax=ax,
            edgelist=edgelist_no_loops,
            width=1.5,
            alpha=0.25,
            edge_color='grey'
        )
    
    # Figure title removed

    norm_min = min(closeness_values) if closeness_values else 0
    norm_max = max(closeness_values) if closeness_values else 1
    if norm_min == norm_max and closeness_values:
        norm_max = norm_min + 0.1 
        if norm_max == 0: 
           norm_max = 1.0
           norm_min = 0.0
        if norm_min == norm_max : 
            norm_min = norm_max - 0.1


    sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=norm_min, vmax=norm_max))
    sm.set_array([])
    
    cbar = fig.colorbar(sm, shrink=0.8, aspect=20, ax=ax, orientation='vertical')
    cbar.set_label('Closeness Centrality', fontsize=60, labelpad=25)
    cbar.ax.tick_params(labelsize=60)
    
    ax.axis('off')
    plt.tight_layout()
    
    output_filename = "graph_closeness_centrality.svg"
    plt.savefig(output_filename, format="svg", bbox_inches='tight')
    print(f"Figure saved to {output_filename}")
    
    plt.show()