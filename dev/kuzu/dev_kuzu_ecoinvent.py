# %%

import csv
import hashlib
import json
import kuzu
import pyecospold
import tempfile
import shutil
import concurrent.futures
import threading
import io
from multiprocessing import Manager

from functools import partial
from lxml import objectify
from pathlib import Path
from tqdm import tqdm
from pyecospold.model_v2 import IntermediateExchange, Activity, FlowData
from greengraph.utility.logging import logtimer

# --- 1. The Producer Thread's job ---
def file_producer(filepaths, queue, num_workers):
    """Reads files from disk and puts their content onto a shared queue."""
    print("▶️  Producer thread started: Reading files from disk...")
    for path in filepaths:
        try:
            content = path.read_bytes()
            queue.put((path.name, content)) # Pass filename for error reporting
        except Exception as e:
            print(f"Could not read file {path}: {e}")
            continue
    print("⏹️  Producer thread finished: All files queued.")
    # Add a "sentinel" value for each worker to signal the end of the queue
    for _ in range(num_workers):
        queue.put(None)

# --- 2. The Consumer Process's job ---
def parse_spold_content(queue, activity_mapping, product_mapping):
    """
    Worker function that gets file content from the queue, parses it, and
    returns all processed results in a single list.
    """
    # Helper functions are defined within the worker's scope
    _ = lambda s: str(s).encode("utf-8")
    def unique_identifier(process_dict, product_dict, type): return hashlib.md5(_(process_dict["name"]) + _(product_dict["name"]) + _(product_dict["unit"]) + _(process_dict["geography"]) + _(type)).hexdigest()
    def get_process_id(edge, activity): return edge.activityLinkId or activity.id
    def reference_product(flows):
        candidates = [edge for edge in flows.intermediateExchanges if edge.groupStr == "ReferenceProduct" and edge.amount != 0]
        if not len(candidates) == 1: raise ValueError("Could not find a single reference product.")
        return candidates[0].intermediateExchangeId
    INPUT_GROUPS = ("Materials/Fuels", "Electricity/Heat", "Services", "From Technosphere (unspecified)")
    
    worker_results = []
    # This loop continues until a sentinel 'None' is received
    while True:
        item = queue.get()
        if item is None:
            break
        
        filename, content = item
        try:
            # Use io.BytesIO to treat the in-memory content as a file
            file_like_object = io.BytesIO(content)
            ecospold = pyecospold.parse_file_v2(file_like_object)

            local_technosphere_edges = []
            local_ecosphere_edges = []

            activity = ecospold.activityDataset.activityDescription.activity[0]
            flow_data = ecospold.activityDataset.flowData

            this_process_attrs = activity_mapping[activity.id]
            this_product_attrs = product_mapping[reference_product(flow_data)]
            this_process_id = unique_identifier(this_process_attrs, this_product_attrs, "process")
            this_product_id = unique_identifier(this_process_attrs, this_product_attrs, "product")

            process_data = {"id": this_process_id, "name": this_process_attrs["name"], "product": this_product_attrs["name"], "unit": this_product_attrs["unit"], "geography": this_process_attrs["geography"], "classifications": this_product_attrs["classifications"]}

            for edge in flow_data.intermediateExchanges:
                if edge.amount and edge.groupStr in INPUT_GROUPS:
                    other_process_attrs = activity_mapping[get_process_id(edge=edge, activity=activity)]
                    other_product_attrs = product_mapping[edge.intermediateExchangeId]
                    other_product_id = unique_identifier(other_process_attrs, other_product_attrs, "product")
                    local_technosphere_edges.append((other_product_id, this_process_id, edge.amount))

            for edge in flow_data.elementaryExchanges:
                if edge.amount:
                    local_ecosphere_edges.append((this_process_id, edge.elementaryExchangeId, edge.amount))
            
            worker_results.append((process_data, local_technosphere_edges, local_ecosphere_edges, this_product_id, this_process_id))
        except Exception as e:
            print(f"Worker failed to parse {filename}: {e}")
            
    return worker_results

def import_ecospold_to_kuzu_pro(ecoinvent_path: Path, db_path: Path):
    """
    Imports EcoSpold to Kuzu using a Producer-Consumer pattern for maximum performance.
    """
    # Master data parsing
    with logtimer('Parsing master data XML files'):
        NS = "{http://www.EcoInvent.org/EcoSpold02}"
        geographies_fp = ecoinvent_path / "MasterData" / "Geographies.xml"
        geographies_mapping = {elem.get("id"): elem.name.text for elem in objectify.parse(str(geographies_fp)).getroot().iterchildren(f"{NS}geography")}
        activity_name_fp = ecoinvent_path / "MasterData" / "ActivityNames.xml"
        activity_names_mapping = {elem.get("id"): elem.name.text for elem in objectify.parse(str(activity_name_fp)).getroot().iterchildren(f"{NS}activityName")}
        special_activity_type_map = {0: "ordinary transforming activity (default)", 1: "market activity", 2: "IO activity", 3: "Residual activity", 4: "production mix", 5: "import activity", 6: "supply mix", 7: "export activity", 8: "re-export activity", 9: "correction activity", 10: "market group"}
        activities_fp = ecoinvent_path / "MasterData" / "ActivityIndex.xml"
        activity_mapping = {elem.get("id"): {"name": activity_names_mapping[elem.get("activityNameId")], "geography": geographies_mapping[elem.get("geographyId")], "start": elem.get("startDate"), "end": elem.get("endDate"), "type": special_activity_type_map[int(elem.get("specialActivityType"))]} for elem in objectify.parse(str(activities_fp)).getroot().iterchildren(f"{NS}activityIndexEntry")}
        products_fp = ecoinvent_path / "MasterData" / "IntermediateExchanges.xml"
        product_mapping = {elem.get("id"): {"name": elem.name.text, "unit": elem.unitName.text, "classifications": json.dumps(dict([(c.classificationSystem.text, c.classificationValue.text) for c in elem.iterchildren(f"{NS}classification")]))} for elem in objectify.parse(str(products_fp)).getroot().iterchildren(f"{NS}intermediateExchange")}
        flows_fp = ecoinvent_path / "MasterData" / "ElementaryExchanges.xml"
        ecosphere_flows_mapping = {elem.get("id"): {"id": elem.get("id"), "name": elem.name.text, "unit": elem.unitName.text, "formula": elem.get("formula") or None, "cas_number": elem.get("casNumber") or None, "compartment": elem.compartment.compartment.text, "subcompartment": elem.compartment.subcompartment.text, "synonyms": [obj.text for obj in elem.iterchildren(f"{NS}synonym")]} for elem in objectify.parse(str(flows_fp)).getroot().iterchildren(f"{NS}elementaryExchange")}

    manager = Manager()
    work_queue = manager.Queue(maxsize=2000)
    
    processes_data, technosphere_edges_data, ecosphere_edges_data = [], [], []
    product_id_to_process_id = {}
    
    with logtimer('Starting Producer-Consumer parsing pipeline'):
        dataset_files = list((ecoinvent_path / "datasets").glob("*.spold"))

        with concurrent.futures.ProcessPoolExecutor() as executor:
            num_workers = executor._max_workers
            producer = threading.Thread(target=file_producer, args=(dataset_files, work_queue, num_workers))
            producer.start()

            parser_func = partial(parse_spold_content, activity_mapping=activity_mapping, product_mapping=product_mapping)
            
            futures = [executor.submit(parser_func, work_queue) for _ in range(num_workers)]
            
            # Use tqdm to show progress as workers complete their batches
            for future in tqdm(concurrent.futures.as_completed(futures), total=num_workers, desc="Processing batches"):
                worker_results = future.result()
                for result in worker_results:
                    process_data, local_technosphere, local_ecosphere, p_id, proc_id = result
                    processes_data.append(process_data)
                    technosphere_edges_data.extend(local_technosphere)
                    ecosphere_edges_data.extend(local_ecosphere)
                    product_id_to_process_id[p_id] = proc_id
            
            producer.join() # Ensure the reader thread has finished

    # --- Automated Cleanup & Bulk Loading ---
    if db_path.exists() and db_path.is_dir():
        print(f"🧹 Deleting existing database at: {db_path}")
        shutil.rmtree(db_path)

    with tempfile.TemporaryDirectory() as tempdir:
        temp_path = Path(tempdir)
        with logtimer(f"Writing temporary CSV files to {temp_path}"):
            # Write Process nodes
            with open(temp_path / "processes.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=processes_data[0].keys())
                writer.writeheader()
                writer.writerows(processes_data)
            # Write Biosphere nodes
            with open(temp_path / "biosphere.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=ecosphere_flows_mapping[list(ecosphere_flows_mapping.keys())[0]].keys())
                writer.writeheader()
                writer.writerows(ecosphere_flows_mapping.values())
            # Write CONSUMES relationships
            with open(temp_path / "consumes.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["_from", "_to", "amount"]) # Special headers for Kuzu
                for p_id, target_id, amount in technosphere_edges_data:
                    source_id = product_id_to_process_id.get(p_id)
                    if source_id:
                        writer.writerow([source_id, target_id, amount])
            # Write EMITS relationships
            with open(temp_path / "emits.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["_from", "_to", "amount"]) # Special headers for Kuzu
                writer.writerows(ecosphere_edges_data)

        with logtimer('Initializing Kuzu and bulk loading from CSV'):
            db = kuzu.Database(str(db_path))
            conn = kuzu.Connection(db)
            
            print("🏗️  Creating database schema...")
            conn.execute("CREATE NODE TABLE Process(id STRING, name STRING, product STRING, unit STRING, geography STRING, classifications STRING, PRIMARY KEY (id))")
            conn.execute("CREATE NODE TABLE Biosphere(id STRING, name STRING, unit STRING, cas_number STRING, formula STRING, compartment STRING, subcompartment STRING, synonyms STRING[], PRIMARY KEY (id))")
            conn.execute("CREATE REL TABLE CONSUMES(FROM Process TO Process, amount DOUBLE)")
            conn.execute("CREATE REL TABLE EMITS(FROM Process TO Biosphere, amount DOUBLE)")
            
            print("🚀 Starting bulk load...")
            conn.execute(f"COPY Process FROM '{temp_path / 'processes.csv'}' (HEADER true)")
            print(f"✔️ Copied {len(processes_data)} Process nodes.")
            conn.execute(f"COPY Biosphere FROM '{temp_path / 'biosphere.csv'}' (HEADER true)")
            print(f"✔️ Copied {len(ecosphere_flows_mapping)} Biosphere nodes.")
            conn.execute(f"COPY CONSUMES FROM '{temp_path / 'consumes.csv'}' (HEADER true)")
            print(f"✔️ Copied technosphere edges.")
            conn.execute(f"COPY EMITS FROM '{temp_path / 'emits.csv'}' (HEADER true)")
            print(f"✔️ Copied ecosphere edges.")

    print("\n✅ Kuzu database import complete.")

# %%

def get_total_edge_count_from_conn(conn: kuzu.Connection) -> int:
    """
    Uses an existing Kuzu connection to return the total number of edges.
    
    Parameters
    ----------
    conn : kuzu.Connection
        An active connection to a Kuzu database.

    Returns
    -------
    int
        The total number of edges in the database.
    """
    try:
        query = "MATCH ()-[r]->() RETURN count(r);"
        result_df = conn.execute(query).get_as_df()
        
        # Extract the single value from the DataFrame
        total_edges = result_df.iloc[0, 0]
        return total_edges
        
    except Exception as e:
        print(f"An error occurred while executing the query: {e}")
        return 0

# %%

# --- How to Run This Script ---
# 1. Save the code above as a Python file (e.g., `import_script.py`).
# 2. IMPORTANT: On Windows and macOS, multiprocessing requires the main logic
#    to be protected by this `if __name__ == "__main__":` block.
# 3. Update the two path variables below to match your system.
# 4. Run from your terminal: python import_script.py
if __name__ == '__main__':
    # === UPDATE THESE PATHS ===
    ECOINVENT_DB_PATH = Path("/path/to/your/ecoinvent 3.x.x_apos_ecoSpold02")
    KUZU_DB_PATH = Path("./ecoinvent.kuzu")
    # ==========================

    import_ecospold_to_kuzu_pro(ECOINVENT_DB_PATH, KUZU_DB_PATH)