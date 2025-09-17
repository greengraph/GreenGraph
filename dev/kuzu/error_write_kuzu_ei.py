# %%
import pandas as pd
import kuzu
import pickle
import os
import shutil

# --- 1. Setup and Data Loading ---
DB_PATH = 'db_error_test.kuzu'

# Clean up previous database instance to ensure a fresh start
if os.path.exists(DB_PATH):
    shutil.rmtree(DB_PATH)
    print(f"Removed old database directory: {DB_PATH}")

# Load your graph data from the pickle file
try:
    with open('/Users/michaelweinold/github/GreenGraph/dev/Geco.pkl', 'rb') as f:
        G = pickle.load(f)
except FileNotFoundError:
    print("Error: Geco.pkl not found. Please ensure the path is correct.")
    exit()

# Convert graph to DataFrames
nodes_data = [{'ID': node, **data} for node, data in G.nodes(data=True)]
nodes_df = pd.DataFrame(nodes_data)

edges_data = [{'source_node_id': u, 'dest_node_id': v, **data} 
              for u, v, data in G.edges(data=True)]
edges_df = pd.DataFrame(edges_data)

print(f"Nodes DataFrame shape: {nodes_df.shape}")
print(f"Edges DataFrame shape: {edges_df.shape}\n")


# --- 2. Kuzu Database and Schema Setup ---
db = kuzu.Database(DB_PATH)
conn = kuzu.Connection(db)

print("Creating Kuzu schema...")
# Node Table
conn.execute("""
    CREATE NODE TABLE Activity(
        ID STRING, type STRING, name STRING, product STRING, unit STRING,
        geography STRING, `geography code` STRING, classifications STRING,
        brightway_code_process STRING, brightway_code_product STRING,
        system STRING, production DOUBLE, chemical_formula STRING, CAS STRING,
        compartment STRING, subcompartment STRING, synonyms STRING,
        brightway_code_extension STRING, PRIMARY KEY (ID)
    )
""")

# Relationship Table
conn.execute("""
    CREATE REL TABLE Flow(
        FROM Activity TO Activity,
        amount DOUBLE,
        type STRING
    )
""")
print("Schema created successfully. ✅\n")


# --- 3. Attempt to Load Entire DataFrames (This should fail) ---

# Attempt to load all nodes at once
print("Attempting to load all nodes in a single transaction (expected to fail)...")
try:
    # The variable 'nodes_df' must be in the local scope for Kuzu to find it
    conn.execute("COPY Activity FROM nodes_df")
    print("✅ Nodes loaded successfully (unexpected).")
except Exception as e:
    print("\n❌ FAILED as expected while loading nodes.")
    print("--- ERROR MESSAGE ---")
    print(e)
    print("---------------------\n")

# Prepare and attempt to load all edges at once
print("Attempting to load all edges in a single transaction (expected to fail)...")
try:
    edges_for_copy = edges_df.rename(columns={
        'source_node_id': '_from',
        'dest_node_id': '_to'
    })
    # The variable 'edges_for_copy' must be in the local scope
    conn.execute("COPY Flow FROM edges_for_copy")
    print("✅ Edges loaded successfully (unexpected).")
except Exception as e:
    print("\n❌ FAILED as expected while loading edges.")
    print("--- ERROR MESSAGE ---")
    print(e)
    print("---------------------\n")


