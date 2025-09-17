# %%
# THIS SEEMS TO FAIL?
import pandas as pd
import numpy as np
import kuzu
import uuid
import os
import shutil
import time

print("--- Kuzu Large DataFrame Load MWE ---", flush=True)

# --- 1. Configuration ---
NUM_NODES = 20_000
NUM_EDGES = 2_000_000
DB_PATH = 'db_synthetic_error.kuzu'
print(f"Configuration: {NUM_NODES} nodes, {NUM_EDGES} edges.", flush=True)

# --- 2. Robust Cleanup ---
if os.path.exists(DB_PATH):
    if os.path.isdir(DB_PATH):
        shutil.rmtree(DB_PATH)
    else:
        os.remove(DB_PATH)
    print(f"Removed old database artifact: {DB_PATH}", flush=True)

# --- 3. Data Generation ---
print("\nGenerating synthetic data...", flush=True)
start_time = time.time()
node_ids = [str(uuid.uuid4()) for _ in range(NUM_NODES)]
nodes_df = pd.DataFrame({
    'ID': node_ids, 'type': 'synthetic_process', 'name': 'placeholder', 'product': 'placeholder',
    'unit': 'kg', 'geography': 'GLO', 'geography code': 'GLO', 'classifications': '[]',
    'brightway_code_process': 'placeholder', 'brightway_code_product': 'placeholder', 'system': 'synthetic',
    'production': 1.0, 'chemical_formula': None, 'CAS': None, 'compartment': 'air',
    'subcompartment': 'unspecified', 'synonyms': None, 'brightway_code_extension': None
})
source_nodes = np.random.choice(node_ids, size=NUM_EDGES, replace=True)
dest_nodes = np.random.choice(node_ids, size=NUM_EDGES, replace=True)
edges_df = pd.DataFrame({
    'source_node_id': source_nodes, 'dest_node_id': dest_nodes,
    'amount': np.random.rand(NUM_EDGES), 'type': 'technosphere'
})
print(f"Data generation finished in {time.time() - start_time:.2f} seconds.", flush=True)
print(f"DataFrame Shapes -> Nodes: {nodes_df.shape}, Edges: {edges_df.shape}\n", flush=True)

# --- 4. Kuzu Setup ---
db = kuzu.Database(DB_PATH)
conn = kuzu.Connection(db)
print("Creating Kuzu schema...", flush=True)
# Use "IF NOT EXISTS" to make this script safely re-runnable
conn.execute("""
    CREATE NODE TABLE IF NOT EXISTS Activity(
        ID STRING, type STRING, name STRING, product STRING, unit STRING,
        geography STRING, `geography code` STRING, classifications STRING,
        brightway_code_process STRING, brightway_code_product STRING,
        system STRING, production DOUBLE, chemical_formula STRING, CAS STRING,
        compartment STRING, subcompartment STRING, synonyms STRING,
        brightway_code_extension STRING, PRIMARY KEY (ID)
    )
""")
conn.execute("""
    CREATE REL TABLE IF NOT EXISTS Flow(
        FROM Activity TO Activity,
        amount DOUBLE,
        type STRING
    )
""")
print("Schema created successfully. ✅\n", flush=True)

# %%

# --- 5. Attempt to Load Entire DataFrames (This should fail) ---
print("Attempting to load all nodes in a single transaction (expected to fail)...", flush=True)
try:
    conn.execute("COPY Activity FROM nodes_df")
    print("✅ Nodes loaded successfully (unexpected).", flush=True)
except Exception as e:
    print("\n❌ FAILED as expected while loading nodes.", flush=True)
    print("--- ERROR MESSAGE ---")
    print(e)
    print("---------------------\n", flush=True)

print("Attempting to load all edges in a single transaction (expected to fail)...", flush=True)
try:
    edges_for_copy = edges_df.rename(columns={'source_node_id': '_from', 'dest_node_id': '_to'})
    conn.execute("COPY Flow FROM edges_for_copy")
    print("✅ Edges loaded successfully (unexpected).", flush=True)
except Exception as e:
    print("\n❌ FAILED as expected while loading edges.", flush=True)
    print("--- ERROR MESSAGE ---")
    print(e)
    print("---------------------\n", flush=True)