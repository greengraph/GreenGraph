# %%

import kuzu
import numpy as np
import pandas as pd
import pyarrow as pa
from scipy.sparse import csr_matrix
import os
import time

# === Configuration ===
NUM_NODES = 10_000
NUM_EDGES = 50_000
DB_PATH = "./kuzu_large_db"
CSV_DIR = "/tmp/kuzu_data"

# =================================================================
# ## 1. Generating and Loading Large-Scale Data
# =================================================================

print(f"--- Step 1: Generating CSV data for {NUM_NODES} nodes and {NUM_EDGES} edges ---")
os.makedirs(CSV_DIR, exist_ok=True)
node_file_path = os.path.join(CSV_DIR, "nodes.csv")
edge_file_path = os.path.join(CSV_DIR, "edges.csv")

# Generate node data
node_ids = np.arange(NUM_NODES)
node_df = pd.DataFrame({'id': node_ids})
node_df.to_csv(node_file_path, index=False)

# Generate edge data
from_ids = np.random.randint(0, NUM_NODES, size=NUM_EDGES)
to_ids = np.random.randint(0, NUM_NODES, size=NUM_EDGES)
# CORRECTED: Use '_from' and '_to' for the column names.
edge_df = pd.DataFrame({'_from': from_ids, '_to': to_ids}) 
edge_df = edge_df[edge_df['_from'] != edge_df['_to']]
edge_df.to_csv(edge_file_path, index=False)

print(f"CSV files created at: {CSV_DIR}")

# --- Kuzu Setup and Bulk Load ---
print("\n--- Step 2: Setting up Kuzu and bulk loading from CSV ---")
start_time = time.time()

db = kuzu.Database(DB_PATH)
conn = kuzu.Connection(db)

conn.execute("CREATE NODE TABLE User(id INT64, PRIMARY KEY (id))")
conn.execute("CREATE REL TABLE Follows(FROM User TO User)")

print("Loading nodes...")
conn.execute(f"COPY User FROM '{node_file_path}'")
print("Loading edges...")
# CORRECTED: Simplified the COPY command.
conn.execute(f"COPY Follows FROM '{edge_file_path}'")

end_time = time.time()
print(f"Data loading complete. Took {end_time - start_time:.2f} seconds.")

# =================================================================
# ## 2. Extracting the Adjacency Matrix
# =================================================================

print("\n--- Step 3: Extracting graph to SciPy Sparse Matrix ---")
start_time = time.time()

nodes_query_result = conn.execute("MATCH (u:User) RETURN u.id ORDER BY u.id")
arrow_table_nodes = nodes_query_result.get_as_arrow()
node_ids_np = arrow_table_nodes.column('u.id').to_numpy()
id_to_idx = {node_id: i for i, node_id in enumerate(node_ids_np)}
num_nodes = len(id_to_idx)

edges_query_result = conn.execute("MATCH (a:User)-[:Follows]->(b:User) RETURN a.id, b.id")
arrow_table_edges = edges_query_result.get_as_arrow()

source_ids_np = arrow_table_edges.column('a.id').to_numpy()
dest_ids_np = arrow_table_edges.column('b.id').to_numpy()
source_indices = np.array([id_to_idx[id] for id in source_ids_np])
dest_indices = np.array([id_to_idx[id] for id in dest_ids_np])
edge_data = np.ones(arrow_table_edges.num_rows, dtype=np.uint8)

adjacency_matrix_sparse = csr_matrix(
    (edge_data, (source_indices, dest_indices)),
    shape=(num_nodes, num_nodes)
)
end_time = time.time()
print(f"Matrix extraction complete. Took {end_time - start_time:.2f} seconds.")

# =================================================================
# ## 3. Verification
# =================================================================

print("\n--- Step 4: Verifying the sparse matrix ---")
print(f"Matrix Shape: {adjacency_matrix_sparse.shape}")
print(f"Number of non-zero elements (edges): {adjacency_matrix_sparse.nnz}")
print(f"Data type of matrix values: {adjacency_matrix_sparse.dtype}")
print("\nSlice of the matrix (top-left 10x10):")
print(adjacency_matrix_sparse[:10, :10].toarray())

# --- Cleanup ---
os.remove(node_file_path)
os.remove(edge_file_path)

# %%
# Polars
%%timeit

# --- Get node mapping ---
nodes_pl = conn.execute("MATCH (u:User) RETURN u.id ORDER BY u.id").get_as_pl()
id_to_idx = {node_id: i for i, node_id in enumerate(nodes_pl.to_series())}
num_nodes = len(id_to_idx)

# --- Get edge list ---
edge_pl = conn.execute("MATCH (a:User)-[:Follows]->(b:User) RETURN a.id, b.id").get_as_pl()

# --- Build the matrix using the CORRECT Polars method ---
# The correct method is .replace(), not .map_dict()
source_indices = edge_pl.get_column('a.id').replace(id_to_idx).to_numpy()
dest_indices = edge_pl.get_column('b.id').replace(id_to_idx).to_numpy()
edge_data = np.ones(len(edge_pl), dtype=np.uint8)

adjacency_matrix_sparse = csr_matrix(
    (edge_data, (source_indices, dest_indices)),
    shape=(num_nodes, num_nodes)
)

# %%
# Pandas

# %%
%%timeit

nodes_df = conn.execute("MATCH (u:User) RETURN u.id ORDER BY u.id").get_as_df()
id_to_idx = {node_id: i for i, node_id in enumerate(nodes_df['u.id'])}
num_nodes = len(id_to_idx)

# --- Get edge list ---
edge_df = conn.execute("MATCH (a:User)-[:Follows]->(b:User) RETURN a.id, b.id").get_as_df()

# --- Build the matrix using Pandas methods ---
source_indices = edge_df['a.id'].map(id_to_idx).to_numpy()
dest_indices = edge_df['b.id'].map(id_to_idx).to_numpy()
edge_data = np.ones(len(edge_df), dtype=np.uint8)

adjacency_matrix_sparse = csr_matrix(
    (edge_data, (source_indices, dest_indices)),
    shape=(num_nodes, num_nodes)
)

# %%
# Pyarrow

# %%
%%timeit

nodes_query_result = conn.execute("MATCH (u:User) RETURN u.id ORDER BY u.id")
arrow_table_nodes = nodes_query_result.get_as_arrow()
node_ids_np = arrow_table_nodes.column('u.id').to_numpy()
id_to_idx = {node_id: i for i, node_id in enumerate(node_ids_np)}
num_nodes = len(id_to_idx)

edges_query_result = conn.execute("MATCH (a:User)-[:Follows]->(b:User) RETURN a.id, b.id")
arrow_table_edges = edges_query_result.get_as_arrow()

source_ids_np = arrow_table_edges.column('a.id').to_numpy()
dest_ids_np = arrow_table_edges.column('b.id').to_numpy()
source_indices = np.array([id_to_idx[id] for id in source_ids_np])
dest_indices = np.array([id_to_idx[id] for id in dest_ids_np])
edge_data = np.ones(arrow_table_edges.num_rows, dtype=np.uint8)

adjacency_matrix_sparse = csr_matrix(
    (edge_data, (source_indices, dest_indices)),
    shape=(num_nodes, num_nodes)
)



