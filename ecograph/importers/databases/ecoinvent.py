# %%
from pathlib import Path
import networkx as nx


def ingest_ecoinvent_from_brightway_datapackage(
    path: Path,
) -> nx.MultiDiGraph: