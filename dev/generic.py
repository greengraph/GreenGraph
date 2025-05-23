# %%
import networkx as nx
import xarray as xr
import numpy as np
import logging
import uuid
from greengraph.core import GreenMultiDiGraph
from greengraph.utility.logging import logtimer
from greengraph.utility.graph import graph_from_matrix

from greengraph.importers.databases.inputoutput import useeio

dct = useeio.load_useeio_data_from_zenodo(version='2.0.1-411')

A = graph_from_matrix(
    matrix=dct['A'],
    nodes_axis_0=dct['dicts_A_metadata'],
    nodes_axis_1=dct['dicts_A_metadata'],
    common_attributes_nodes_axis_0={},
    common_attributes_nodes_axis_1={},
    name_amount_attribute='flow',
    common_attributes_edges={},
    create_using=GreenMultiDiGraph,
)