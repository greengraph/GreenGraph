# %%
import networkx as nx
import numpy as np
import scipy as sp
import xarray as xr
import logging
from greengraph.utility.logging import logtimer


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
        dims=A.dims[0],
        coords={A.dims[0]: A.coords[A.dims[0]]}
    )

    return x


def calculate_inventory_vectors(
    x: xr.DataArray,
    B: xr.DataArray
) -> xr.DataArray:
    dict_inventory_vectors_by_system = {}
    for system in np.unique(B.coords['system'].values):
        B_system = B.sel(col={'system': system})
        x_system = x.sel(row={'system': system})
        g_system = xr.DataArray(
            B_system.data @ x_system.data,
            dims=('rows'),
            coords={
                'rows': B.coords['rows'].values
            }
        )
        dict_inventory_vectors_by_system[system] = g_system
    
    return dict_inventory_vectors_by_system


def calculate_impact_vectors(
    dict_g: dict,
    Q: xr.DataArray,
    impact_category: str,
) -> xr.DataArray:
    for system, g in dict_g.items():
        