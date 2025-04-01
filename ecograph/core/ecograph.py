import numpy as np
import pandas as pd
import xarray as xr
import networkx as nx
from datetime import datetime
from typing import Any, Literal
import uuid


class CustomMultiDiGraph(nx.MultiDiGraph):
    r"""
    A custom directed graph class that extends [networkx.MultiDiGraph](https://networkx.org/documentation/stable/reference/classes/multidigraph.html).

    Every node in the graph has the following attributes:

    | Attribute   | Type   | Description                               | Req.? | Possible Values | 
    |-------------|--------|-------------------------------------------|-----------|------------|
    | type        | str    | Type of the node (e.g., `process`, `sector`) | ❌ | None, can be any string |
    | name        | str    | Name of the node (e.g., `Electricity production`) | ✅ | None, can be any string |
    | product     | str    | Product associated with the node (e.g., 'Electricity') | ✅ | None, can be any string |
    | location    | str    | Location of the node (e.g., 'USA')      | ❌ | None, can be any string |
    | amount      | float  | Amount associated with the node (e.g., 1000) | ✅ | None, can be any float |
    | unit        | str    | Unit of the amount (e.g., 'GWh')        | ❌ | None, can be any string |
    | loops       | bool   | Whether the node has loops (default: False) | ❌ | True, False |
    | edges       | bool   | Whether the node has edges (default: False) | ❌ | True, False |
    | database    | str    | Database associated with the node (e.g., 'Ecoinvent') | ❌ | None, can be any string |
    | databasecode| str    | Database code associated with the node (e.g., 'Ecoinvent 3.8') | ❌ | None, can be any string |
    | metadata    | dict   | Additional metadata for the node (default: empty dict) | ❌ | None, can be any dictionary |

    Note that every node on the graph is uniquely identified by [a random UUID (`uuid4`)](https://en.wikipedia.org/wiki/Universally_unique_identifier#Version_4_(random)).
    This identifier is generated automatically when the node is added to the graph.
    
    All NetworkX methods of the MultiDiGraph class are available. Only the `add_node` and `add_edge` methods are overridden to include these custom attributes.

    Notes
    -----
    ### `loop` Parameter

    There are two different conventions in 

    If `loops=True`, the elements $a_{ii}$ of the adjacency matrix (eg. technosphere matrix) describe a flow from node $i$ to itself, which indicates _self-consumption_.  
    If `loops=False`, the elements $a_{ij}$ of the adjacency matrix (eg. technical coefficient matrix) indicate the production of the output of node $i$.

    $$
    \mathbf{I} - \mathbf{A}
    $$

    and

    $$
    \mathbf{A}
    $$

    ### `edges` Parameter

    Input-output tables are generally very dense. This means that most of the elements in the adjacency matrix are non-zero.
    A table of ~10'000 sectors can therefore have ~300'000 edges.
    Storing all edges of such a system in a graph can therefore require a lot of memory.

    The `edges` parameter allows to retain edges in the matrix, without the need to add it to the graph.

    See Also
    --------
    [`networkx.MultiDiGraph`](https://networkx.org/documentation/stable/reference/classes/multidigraph.html)

    References
    ----------
    Heijungs, Reinout, Yi Yang, and Hung-Suck Park.  
    "A or I-A? Unifying the computational structures of process-and IO-based LCA for clarity and consistency."  
    _Journal of Industrial Ecology_
    26.5 (2022): 1824-1836.  
    doi:[10.1111/jiec.13323](https://doi.org/10.1111/jiec.13323)

    """
    def add_node(
        self,
        type: str,
        name: str,
        product: str,
        location: str,
        amount: float,
        unit: str,
        loops: bool = False,
        edges: bool = False,
        database: str = None,
        databasecode: str = None,
        metadata: dict = None,
    ) -> None:
        """Add a node with custom attributes to the graph."""
        node_data = {
            'uuid': str(uuid.uuid4()),
            'type': type,
            'name': name,
            'product': product,
            'location': location,
            'amount': amount,
            'unit': unit,
            'loops': loops,
            'edges': edges,
            'database': database,
            'databasecode': databasecode,
            'metadata': metadata or {}
        }
        super().add_node(name, **node_data)