# %%
import pickle
import pandas as pd

with open('/Users/michaelweinold/github/GreenGraph/dev/Geco.pkl', 'rb') as f:
    Geco = pickle.load(f)

# %%

G = Geco
# %%

# 1. Extract Nodes into a DataFrame
# We create a list of dictionaries, one for each node.
# The node ID is explicitly added to a column named 'ID' to match our schema.
nodes_data = [{'ID': node, **data} for node, data in G.nodes(data=True)]
nodes_df = pd.DataFrame(nodes_data)
print("--- Nodes DataFrame ---")
print(nodes_df)

# 2. Extract Edges into a DataFrame
# We iterate through all edges, capturing source, destination, and attributes.
# The source and destination nodes are named to match Kuzu's expected input.
edges_data = [{'source_node_id': u, 'dest_node_id': v, **data} 
              for u, v, data in G.edges(data=True)]
edges_df = pd.DataFrame(edges_data)
print("\n--- Edges DataFrame ---")
print(edges_df)

# %%

import kuzu

db = kuzu.Database('db.kuzu')
conn = kuzu.Connection(db)

# 1. Define Node Table Schema with corrected quoting
print("Defining schema with corrected backticks (`)...")
conn.execute("""
    CREATE NODE TABLE Activity(
        ID STRING,
        type STRING,
        name STRING,
        product STRING,
        unit STRING,
        geography STRING,
        `geography code` STRING,
        classifications STRING,
        brightway_code_process STRING,
        brightway_code_product STRING,
        system STRING,
        production DOUBLE,
        chemical_formula STRING,
        CAS STRING,
        compartment STRING,
        subcompartment STRING,
        synonyms STRING,
        brightway_code_extension STRING,
        PRIMARY KEY (ID)
    )
""")
print("Node table 'Activity' created successfully. ✅")


# 2. Define Relationship Table Schema (this was already correct)
conn.execute("""
    CREATE REL TABLE Flow(
        FROM Activity TO Activity,
        amount DOUBLE,
        type STRING
    )
""")

# %%

import numpy as np

# Adjust this chunk size based on your available RAM and DataFrame size
# Start with a number like 50,000 or 100,000
chunk_size = 1000

# Calculate the number of chunks
num_chunks = len(nodes_df) // chunk_size + 1

print(f"Splitting DataFrame into {num_chunks} chunks of size {chunk_size}...")

for i, chunk in enumerate(np.array_split(nodes_df, num_chunks)):
    print(f"Loading chunk {i+1} of {num_chunks} ({len(chunk)} rows)...")
    
    # Kuzu's 'COPY FROM' can find the 'chunk' variable in the local scope
    conn.execute("COPY Activity FROM chunk")

print("\nAll chunks loaded successfully. ✅")
# %%

# 1. Rename columns for Kuzu's COPY command
print("Renaming edge columns to '_from' and '_to'...")
edges_for_copy = edges_df.rename(columns={
    'source_node_id': '_from',
    'dest_node_id': '_to'
})
print("Columns renamed successfully.")

# 2. Set the small chunk size and load in batches
chunk_size = 1000
num_chunks = len(edges_for_copy) // chunk_size + 1

print(f"\nSplitting edges into {num_chunks} chunks...")
for i, chunk in enumerate(np.array_split(edges_for_copy, num_chunks)):
    print(f"Loading edge chunk {i+1} of {num_chunks} ({len(chunk)} rows)...")
    conn.execute("COPY Flow FROM chunk")

print("\nAll edge chunks loaded successfully. ✅")


# %%

import pyarrow as pa
from scipy.sparse import csr_matrix

def build_csr():
    print("\n--- Step 3: Creating SciPy CSR Matrix ---")
    # Get edge list as a PyArrow Table
    print("Fetching edges...")
    edges_query = conn.execute(
        "MATCH (a:Activity)-[:Flow]->(b:Activity) RETURN a.ID AS source, b.ID AS destination"
    )
    edges_arrow_table = edges_query.get_as_arrow()

    # Create the integer index mapping for the matrix
    print("Fetching node IDs for index mapping...")
    all_nodes_query = conn.execute("MATCH (a:Activity) RETURN a.ID")
    all_node_ids = all_nodes_query.get_as_arrow().column('a.ID').to_numpy()
    id_to_idx = {node_id: i for i, node_id in enumerate(all_node_ids)}
    num_nodes = len(all_node_ids)

    # Extract columns and map string IDs to integer indices
    print("Mapping IDs to integer indices...")
    source_ids_np = edges_arrow_table.column('source').to_numpy()
    dest_ids_np = edges_arrow_table.column('destination').to_numpy()
    source_indices = np.array([id_to_idx[id] for id in source_ids_np])
    dest_indices = np.array([id_to_idx[id] for id in dest_ids_np])

    # For a simple adjacency matrix, edge data is all 1s
    edge_data = np.ones(len(source_indices), dtype=np.uint8)

    # Create the final sparse matrix
    print("Creating SciPy CSR matrix...")
    adjacency_matrix_sparse = csr_matrix(
        (edge_data, (source_indices, dest_indices)),
        shape=(num_nodes, num_nodes)
    )
    return adjacency_matrix_sparse

def build_csr_2():
    # --- Fetch data (same as before) ---
    edges_arrow_table = conn.execute(
        "MATCH (a:Activity)-[:Flow]->(b:Activity) RETURN a.ID AS source, b.ID AS destination"
    ).get_as_arrow()

    all_node_ids_unsorted = conn.execute(
        "MATCH (a:Activity) RETURN a.ID"
    ).get_as_arrow().column('a.ID').to_numpy()

    source_ids_np = edges_arrow_table.column('source').to_numpy()
    dest_ids_np = edges_arrow_table.column('destination').to_numpy()

    # --- Optimized Mapping ---
    print("Optimizing map creation with np.searchsorted...")

    # 1. Sort the array of all unique node IDs. This is required for searchsorted.
    all_node_ids_sorted = np.sort(all_node_ids_unsorted)
    num_nodes = len(all_node_ids_sorted)

    # 2. Use np.searchsorted to find the integer indices. This is much faster.
    source_indices = np.searchsorted(all_node_ids_sorted, source_ids_np)
    dest_indices = np.searchsorted(all_node_ids_sorted, dest_ids_np)

    # --- Create Matrix (same as before) ---
    edge_data = np.ones(len(source_indices), dtype=np.uint8)

    adjacency_matrix_sparse = csr_matrix(
        (edge_data, (source_indices, dest_indices)),
        shape=(num_nodes, num_nodes)
    )

    print("\nSciPy CSR matrix created successfully via optimized method:")
    return adjacency_matrix_sparse

def build_csr_3():
    # Step 1: Fetch all unique node IDs into a NumPy array.
    all_nodes_result = conn.execute("MATCH (n:Activity) RETURN n.ID")
    # Get column name robustly in case Kuzu auto-aliases it
    node_id_col_name = all_nodes_result.get_as_arrow().schema.names[0]
    all_node_ids = all_nodes_result.get_as_arrow().column(node_id_col_name).to_numpy()

    # Step 2: Sort the IDs using NumPy.
    sorted_ids = np.sort(all_node_ids)
    num_nodes = len(sorted_ids)

    # Step 3: Execute the edge query, passing the sorted array as a parameter.
    # The '$ids' is a placeholder that will be replaced by the 'sorted_ids' Python variable.
    parameterized_query = """
        MATCH (a:Activity)-[:Flow]->(b:Activity)
        RETURN
            indexOf($ids, a.ID) AS source_idx,
            indexOf($ids, b.ID) AS dest_idx
    """

    indices_table = conn.execute(
        parameterized_query,
        parameters={"ids": sorted_ids}
    ).get_as_arrow()

    # The rest of the code remains the same
    source_indices = indices_table.column('source_idx').to_numpy()
    dest_indices = indices_table.column('dest_idx').to_numpy()
    edge_data = np.ones(len(source_indices), dtype=np.uint8)

    adjacency_matrix_sparse = csr_matrix(
        (edge_data, (source_indices, dest_indices)),
        shape=(num_nodes, num_nodes)
    )
    return adjacency_matrix_sparse

# SEARCH

%%timeit
search_name = "market for waste polyurethane"
search_geography = "Netherlands"

# The Cypher query uses placeholders for the parameters
query = """
    MATCH (n:Activity)
    WHERE n.name = $name AND n.geography = $geo
    RETURN n.name, n.product, n.geography, n.ID
"""

# Execute the query, passing the Python variables as parameters
result_df = conn.execute(
    query,
    parameters={
        "name": search_name,
        "geo": search_geography
    }
)