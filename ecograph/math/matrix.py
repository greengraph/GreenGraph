# %%
import networkx as nx
import numpy as np
import scipy as sp
import xarray as xr
import logging
from ecograph.utility.logging import logtimer


def calculate_production_vector(
    A: xr.DataArray,
    demand: dict[str, float],
) -> xr.DataArray:
    """
    Calculate the production vector of a system given its adjacency matrix and flow vector.

    Parameters
    ----------
    A : np.ndarray
        Adjacency matrix representing the system.
    f : np.ndarray
        Flow vector.

    Returns
    -------
    np.ndarray
        Inventory vector.
    """
    f = np.zeros(A.data.shape[0])
    for node, value in demand.items():
        if node in A.coords['rows'].values:
            f[A.coords['rows'].values == node] = value
        else:
            raise ValueError(f"Node {node} not present in technosphere matrix.")

    if not isinstance(A.data, np.ndarray):
        raise TypeError("A.data must be a numpy array.")
    if sp.issparse(A.data):
        with logtimer("Calculating production vector."):
            x = sp.sparse.linalg.spsolve(np.eye(A.data.shape[0]) - A.data, f)
    else:
        with logtimer("Calculating production vector."):
            x = np.linalg.solve(np.eye(A.data.shape[0]) - A.data, f)

    x = xr.DataArray(
            x,
            dims=('rows'),
            coords={
                'rows': A.coords['rows'].values
            }
    )

    return x


def calculate_inventory_vector(
    x: xr.DataArray,
    B: xr.DataArray
) -> xr.DataArray:
    g = B.data @ x.data
    g = xr.DataArray(
        g,
        dims=('rows'),
        coords={
            'rows': B.coords['rows'].values
        }
    )
    return g


def calculate_impact_vector(
    g: xr.DataArray,
    Q: xr.DataArray
) -> xr.DataArray:
    