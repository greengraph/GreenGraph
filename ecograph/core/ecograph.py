import numpy as np
import pandas as pd
import xarray as xr
import networkx as nx
from datetime import datetime
from typing import Any, Literal
import uuid

class ecograph:
    """
    A class representing a directed graph for ecological networks.

    Inherits from networkx.DiGraph and adds methods for calculating production and inventory vectors.

    Parameters
    ----------
    data : dict, optional
        A dictionary containing the graph data. If not provided, an empty graph is created.
    """
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.metadata = {
            'created': datetime.now(),
            'comment': None,
        }

    def add_node(
        self,
        type: str,
        name: str,
        product: str,
        location: str,
        amount: float,
        unit: str,
        loops: bool = False,
        database: str = None,
        databasecode: str = None,
        metadata: dict = None,
    ) -> None:
        r"""

        See Also
        --------
        [networkx.MultiDiGraph.add_node()](https://networkx.org/documentation/stable/reference/classes/generated/networkx.MultiDiGraph.add_node.html#multidigraph-add-node)
        """
        self.graph.add_node(
            {
                'uuid': str(uuid.uuid4()),
                'type': type,
                'loop': 
                'database': database,
                'metadata': metadata
            }
        )

    def add_edge(
        self,
        u_for_edge: str,
        v_for_edge: str,
        key: Literal["concordance", "flow"],
        value: float,
        metadata: dict = None,
    ) -> None:
        r"""
        See Also
        --------
        [networkx.MultiDiGraph.add_edge()](https://networkx.org/documentation/stable/reference/classes/generated/networkx.MultiDiGraph.add_edge.html#networkx.MultiDiGraph.add_edge)
        """
        self.graph.add_edge(
            u_for_edge=u_for_edge,
            v_for_edge=v_for_edge,
            key=key,
            value=value,
            metadata=metadata
        )