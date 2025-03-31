import numpy as np
import pandas as pd
import xarray as xr
import networkx as nx

class ecograph(nx.DiGraph):
    """
    A class representing a directed graph for ecological networks.

    Inherits from networkx.DiGraph and adds methods for calculating production and inventory vectors.

    Parameters
    ----------
    data : dict, optional
        A dictionary containing the graph data. If not provided, an empty graph is created.
    """
    
    def __init__(self, data=None):
        super().__init__(data)
        self._production_vector = None
        self._inventory_vector = None



"""

{
    'uuid': '12345',
    'hash': 'abcde12345',
    'type': 'process',
    'database': 'ecoinvent',
    'metadata': {
        'unit': 'kg',
        'location': 'CH',
        'type': 'process',
        'functional unit': 'output',
        'name': 'process name',
    }
}


    

"""