# %%
import networkx as nx
import numpy as np
import scipy as sp
import xarray as xr
import logging
from greengraph.utility.logging import logtimer

"""
My fantastic module docstring
"""

def calculate_production_vector(
    A: xr.DataArray,
    demand: dict[str, float],
) -> xr.DataArray:
    r"""
    Given an A-matrix $\mathbf{A}$ and a dictionary of final demand $\vec{f}$,
    calculate the production vector $\vec{x}$ of a system.

    Implements the equation

    $$
    \vec{x} = (\mathbf{I} - \mathbf{A})^{-1} \cdot \vec{f}
    $$

    where

    | Symbol       | Dimension    | Description          |
    |--------------|--------------|----------------------|
    | $\vec{x}$    | $N \times 1$ | Production vector    |
    | $\mathbf{A}$ | $N \times N$ | A-matrix             |
    | $\mathbf{I}$ | $N \times N$ | Identity matrix      |
    | $\vec{f}$    | $N \times 1$ | Final demand vector  |

    and

    | Index | Description                   |
    |-------|-------------------------------|
    | $N$   | Number of nodes in the system |

    Warnings
    --------
    Uses the $(\mathbf{I} - \mathbf{A})$ convention.

    References
    ----------
    - [Eqn.(2.11) in Miller & Blair (3rd Edition, 2022)](https://doi.org/10.1017/9781108676212)  
    - [Eqn.(5.15) in Heijungs & Suh (2002)](https://doi.org/10.1007/978-94-015-9900-9)  
    - Heijungs, Reinout, Yi Yang, and Hung-Suck Park.
    "A or I-A? Unifying the computational structures of process-and IO-based LCA for clarity and consistency."
    _Journal of Industrial Ecology_ 26.5 (2022): 1824-1836.
    doi:[10.1111/jiec.13323](https://doi.org/10.1111/jiec.13323)

    Parameters
    ----------
    A : np.ndarray
        A-matrix $\mathbf{A}$ of the system.  
        $\text{dim}(\mathbf{A})=[N \times N]$
    demand: dict[str, float]
        Dictionary of final demand $\vec{f}$.  

        | keys        | values        |
        |-------------|---------------|
        | node `uuid` | demand amount |

    Returns
    -------
    np.ndarray
        Production vector $\vec{x}$.  
        $\text{dim}(\vec{x})=[N \times 1]$
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
        dims=('rows', 'cols'),
        coords={
            'rows': A.coords['rows'].values,
            'cols': None
        }
    )

    return x


def calculate_inventory_vector(
    x: xr.DataArray,
    B: xr.DataArray,
) -> xr.DataArray:
    r"""
    Given a production vector $\vec{x}$ and a B-matrix $\mathbf{B}$,
    calculate the inventory vector $\vec{g}$ of a system.

    Implements the equation

    $$
    \vec{g} = \mathbf{B} \cdot \vec{x}
    $$

    where

    | Symbol       | Dimension    | Description          |
    |--------------|--------------|----------------------|
    | $\vec{x}$    | $N \times 1$ | Production vector    |
    | $\mathbf{B}$ | $R \times N$ | B-matrix             |
    | $\vec{g}$    | $R \times 1$ | Inventory vector     |

    and

    | Index | Description                            |
    |-------|----------------------------------------|
    | $N$   | Number of rows/columns in the A-matrix |
    | $R$   | Number of rows in the B-matrix         |

    Notes
    -----
    Process-based life-cycle assessment (PLCA) and input-output analysis (IOA)
    use different terminology for the matrices involved in this calculation:

    | Matrix       | Terminology (PLCA)  | Terminology (IOA)                |
    |--------------|---------------------|----------------------------------|
    | $\mathbf{A}$ | Technosphere matrix | Technology matrix                |
    | $\mathbf{B}$ | Biosphere matrix    | (Environmental) satellite matrix |

    References
    ----------
    - [Eqn.(13.3) in Miller & Blair (3rd Edition, 2022)](https://doi.org/10.1017/9781108676212)  
    - [Eqn.(5.15) in Heijungs & Suh (2002)](https://doi.org/10.1007/978-94-015-9900-9)  

    Parameters
    ----------
    x : np.ndarray
        Production vector $\vec{x}$ of the system.  
        $\text{dim}(\vec{x})=[N \times 1]$
    B : np.ndarray
        B-matrix $\mathbf{B}$ of the system.  
        $\text{dim}(\mathbf{B})=[R \times N]$
    
    Returns
    -------
    np.ndarray
        Inventory vector $\vec{g}$.  
        $\text{dim}(\vec{g})=[R \times 1]$
    """
    if not isinstance(x.data, np.ndarray):
        raise TypeError("x.data must be a numpy array.")
    if not isinstance(B.data, np.ndarray):
        raise TypeError("B.data must be a numpy array.")
    if not np.array_equal(B.coords['cols'].values, x.coords['rows'].values):
        raise ValueError("Columns of B and rows of x do not align!")

    g = xr.DataArray(
        data=B.data @ x.data,
        dims=('rows', 'cols'),
        coords={
            'rows': B.coords['rows'].values,
            'cols': None
        }
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
    r"""
    Given an inventory vector $\vec{g}$ and a characterization matrix $\mathbf{Q}$,
    calculate the impact vector $\vec{h}$ of a system.

    Implements the equation

    $$
    \vec{h} = \mathbf{Q} \cdot \vec{g}
    $$

    where

    | Symbol       | Dimension    | Description             |
    |--------------|--------------|-------------------------|
    | $\vec{g}$    | $R \times 1$ | Inventory vector        |
    | $\mathbf{Q}$ | $L \times R$ | Characterization matrix |
    | $\vec{h}$    | $L \times 1$ | Impact vector           |

    and

    | Index | Description                            |
    |-------|----------------------------------------|
    | $L$   | Number of impact categories            |
    | $R$   | Number of rows in the B-matrix         |

    References
    ----------
    - [Eqn.(XXXX) in Miller & Blair (3rd Edition, 2022)](https://doi.org/10.1017/9781108676212)  
    - Eqn.(8.26) in [Heijungs & Suh (2001)](https://doi.org/10.1007/978-94-015-9900-9), but see also ⚠️:
    - Eqn.(8.26) in [Errata of Heijungs & Suh (2001)](https://web.archive.org/web/20230505051343/https://personal.vu.nl/r.heijungs/computational/The%20computational%20structure%20of%20LCA%20-%20Errata.pdf)

    Parameters
    ----------
    g : np.ndarray
        Inventory vector $\vec{g}$ of the system.  
        $\text{dim}(\vec{g})=[R \times 1]$
    Q : np.ndarray
        Characterization matrix $\mathbf{Q}$ of the system.  
        $\text{dim}(\mathbf{Q})=[L \times R]$

    Returns
    -------
    np.ndarray
        Impact vector $\vec{h}$.  
        $\text{dim}(\vec{h})=[L \times 1]$
    """
    if not isinstance(g.data, np.ndarray):
        raise TypeError("g.data must be a numpy array.")
    if not isinstance(Q.data, np.ndarray):
        raise TypeError("Q.data must be a numpy array.")
    if not np.array_equal(Q.coords['cols'].values, g.coords['rows'].values):
        raise ValueError("Rows of Q and rows of g do not align!")

    h = xr.DataArray(
        data=Q.data @ g.data,
        dims=('rows', 'cols'),
        coords={
            'rows': Q.coords[Q.dims[0]],
            'cols': None
        }
    )

    return h
# %%
