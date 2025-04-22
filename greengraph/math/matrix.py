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
    f = np.zeros((A.data.shape[0], 1))
    for node, value in demand.items():
        if np.isin(node, A.coords['rows'].values):
            f[A.coords['rows'].values == node] = value
        else:
            raise ValueError(f"Node {node} not present in technosphere matrix.")

    if not isinstance(A.data, np.ndarray):
        raise TypeError("A.data must be a numpy array.")
    if sp.sparse.issparse(A.data):
        with logtimer("calculating production vector."):
            x = sp.sparse.linalg.spsolve(np.eye(A.data.shape[0]) - A.data, f)
    else:
        with logtimer("calculating production vector."):
            x = np.linalg.solve(np.eye(A.data.shape[0]) - A.data, f)

    x = xr.DataArray(
        x,
        dims=A.dims[0],
        coords={A.dims[0]: A.coords[A.dims[0]]}
    )

    return x


def calculate_inventory_vector(
    x: xr.DataArray,
    B: xr.DataArray,
) -> xr.DataArray:
    """
    Some description here!
    """
    if not isinstance(x.data, np.ndarray):
        raise TypeError("x.data must be a numpy array.")
    if not isinstance(B.data, np.ndarray):
        raise TypeError("B.data must be a numpy array.")
    if not np.array_equal(B.coords['cols'].values, x.coords['rows'].values):
        raise ValueError("Columns of B and rows of x do not align!")

    g = xr.DataArray(
        data=B.data @ x.data,
        dims=B.dims[0],
        coords={B.dims[0]: B.coords[B.dims[0]]}
    )

    return g


def calculate_inventory_vectors(
    x: xr.DataArray,
    inventory_split: dict[str, list[str]],
    B: xr.DataArray,
) -> xr.DataArray:
    """
    abcd
    """
    list_arrays_split_vector = [
        x.where(
            cond=x.coords['rows'].isin(set(inventory_split[system])),
            other=0.0
        )
        for system in inventory_split.keys()
    ]

    # Concatenate along 'system' dimension
    x_matrix = xr.concat(
        objs=list_arrays_split_vector,
        dim='system'
    )

    # Transpose to make 'rows' the first dimension and 'system' the second
    x_matrix = x_matrix.T

    # Create g_matrix with the corrected x_matrix
    g_matrix = xr.DataArray(
        data=B.data @ x_matrix.data,
        dims=('system', 'rows'),
        coords={
            'system': inventory_split.keys(),
            'rows': B.coords['rows'].values
        }
    )

    return g_matrix


def calculate_impact_vector(
    g: xr.DataArray,
    Q: xr.DataArray,
) -> xr.DataArray:
    """
    Calculate the impact vector of a system given its inventory vector and characterization matrix.
    """
    if not isinstance(g.data, np.ndarray):
        raise TypeError("g.data must be a numpy array.")
    if not isinstance(Q.data, np.ndarray):
        raise TypeError("Q.data must be a numpy array.")
    if not np.array_equal(Q.coords['cols'].values, g.coords['rows'].values):
        raise ValueError("Rows of Q and rows of g do not align!")

    h = xr.DataArray(
        data=Q.data @ g.data,
        dims=Q.dims[0],
        coords={Q.dims[0]: Q.coords[Q.dims[0]]}
    )

    return h