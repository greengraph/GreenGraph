"""This module provides matrix operations for the greengraph package.

It includes utilities for matrix manipulation and calculations.
"""

# %%

import networkx as nx
import numpy as np
import scipy as sp
import xarray as xr
from greengraph.utility.logging import logtimer

def calculate_production_vector(
    A: xr.DataArray,
    demand: dict[str, float],
) -> xr.DataArray:
    r"""
    Given an A-matrix $\mathbf{A}$ and a dictionary of final demand $\vec{f}$,
    calculates the production vector $\vec{x}$ of a system.

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
    f = np.zeros(A.data.shape[0])

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
        dims='rows',
        coords={
            'rows': A.coords['rows'].values,
        }
    )

    return x


def calculate_inventory_vector(
    x: xr.DataArray,
    B: xr.DataArray,
) -> xr.DataArray:
    r"""
    Given a production vector $\vec{x}$ and a B-matrix $\mathbf{B}$,
    calculates the inventory vector $\vec{g}$ of a system.

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
        dims='rows',
        coords={
            'rows': B.coords['rows'].values,
        }
    )

    return g


def calculate_impact_vector(
    g: xr.DataArray,
    Q: xr.DataArray,
) -> xr.DataArray:
    r"""
    Given an inventory vector $\vec{g}$ and a characterization matrix $\mathbf{Q}$,
    calculates the impact vector $\vec{h}$ of a system.

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
        dims='rows',
        coords={
            'rows': Q.coords[Q.dims[0]],
        }
    )

    return h


def calculate_inventory_matrix(
    x: xr.DataArray,
    inventory_split: dict[str, list[str]],
    B: xr.DataArray,
) -> xr.DataArray:
    r"""
    Given a production vector $\vec{x}$, a dictionary of
    node categories with associated node `uuid`s and a B-matrix $\mathbf{B}$,
    calculates the inventory vectors $\vec{g}_i$ of a system.
    
    In an example system of 4 nodes, we have the following production vector:

    $$
    \vec{x} = \begin{bmatrix}
        10.01 \\
        20.02 \\
        30.03 \\
        40.04 \\
    \end{bmatrix} {\color{gray}\begin{bmatrix}
        \texttt{abc123} \\
        \texttt{def456} \\
        \texttt{ghi789} \\
        \texttt{jkl012} \\
    \end{bmatrix}}
    $$

    where nodes `[abc123, def456]` belong to the first category, and nodes `[ghi789, jkl012]` to the second category.
    
    This functions splits up the production vector $\vec{x}$ into a matrix $\mathbf{x}$,
    where each column contains the production of nodes beloging to a single category:

    $$
    \mathbf{x} = \begin{bmatrix}
        1.24 & 0.00 \\
        2.34 & 0.00 \\
        0.00 & 3.45 \\
        0.00 & 4.56 \\
    \end{bmatrix}
    $$

    Instead of an inventory vector $\vec{b}$, a matrix of inventory vectors $\mathbf{g}$
    is then computed according to

    $$
    \mathbf{g} = \mathbf{B} \cdot \mathbf{x}
    $$

    giving a matrix of inventory vectors $\mathbf{g}$:

    $$
    \mathbf{g} = \begin{bmatrix}
        1.23 & 6.54 \\
        2.34 & 7.65 \\
        3.45 & 8.76 \\
    \end{bmatrix}
    $$

    where

    | Symbol       | Dimension    | Description          |
    |--------------|--------------|----------------------|
    | $\mathbf{g}$ | $R \times C$ | Inventory matrix     |
    | $\mathbf{B}$ | $R \times N$ | B-matrix             |
    | $\mathbf{x}$ | $N \times C$ | Production matrix    |

    and

    | Index | Description                            |
    |-------|----------------------------------------|
    | $N$   | Number of nodes in the system          |
    | $R$   | Number of rows in the B-matrix         |
    | $C$   | Number of categories                   |


    Notes
    -----
    Summing the inventory matrix $\mathbf{g}$ along the columns (`axis=1`)
    returns the inventory vector $\vec{g}$.

    See Also
    --------
    [`greengraph.math.matrix.calculate_inventory_vector`][]

    Parameters
    ----------
    x : np.ndarray
        Production vector $\vec{x}$ of the system.  
        $\text{dim}(\vec{x})=[N \times 1]$
    inventory_split : dict[str, list[str]]
        Dictionary of inventory split.  

        | keys        | values        |
        |-------------|---------------|
        | category    | list of nodes |

    B : np.ndarray
        B-matrix $\mathbf{B}$ of the system.  
        $\text{dim}(\mathbf{B})=[R \times N]$

    Returns
    -------
    np.ndarray
        Inventory vector $\mathbf{g}$.  
        $\text{dim}(\mathbf{g})=[R \times C]$
    """

    x_matrix = xr.DataArray(
        data=np.zeros(
            shape=(
                x.sizes['rows'],
                len(inventory_split)
            )
        ),
        dims=('rows', 'cols'),
        coords={
            'rows': x.coords['rows'].values,
            'cols': list(inventory_split.keys())
        }
    )

    for split_category, list_nodes in inventory_split.items():
        x_matrix.loc[dict(rows=list_nodes, cols=split_category)] = x.loc[list_nodes]

    g_matrix = xr.DataArray(
        data=B.data @ x_matrix.data,
        dims=('rows', 'cols'),
        coords={
            'rows': B.coords['rows'].values,
            'cols': list(inventory_split.keys())
        }
    )

    return g_matrix


def calculate_impact_matrix(
    g_matrix: xr.DataArray,
    Q: xr.DataArray,
) -> xr.DataArray:
    r"""
    Given an inventory matrix $\mathbf{g}$ and a characterization matrix $\mathbf{Q}$,
    calculates the matrix of impact vectors $\mathbf{h}$ of a system.

    Continuing the example from [`greengraph.math.matrix.calculate_inventory_matrix`][],
    for the matrix of inventory vectors $\mathbf{g}$:

    $$
    \mathbf{g} = \begin{bmatrix}
        1.23 & 6.54 \\
        2.34 & 7.65 \\
        3.45 & 8.76 \\
    \end{bmatrix}
    $$

    The function computes the matrix of impact vectors $\mathbf{h}$:

    $$
    \mathbf{h} = \mathbf{Q} \cdot \mathbf{g}
    $$

    where

    | Symbol       | Dimension    | Description             |
    |--------------|--------------|-------------------------|
    | $\mathbf{g}$ | $R \times C$ | inventory matrix        |
    | $\mathbf{Q}$ | $L \times R$ | characterization matrix |
    | $\mathbf{x}$ | $N \times C$ | production matrix       |

    and

    | Index | Description                            |
    |-------|----------------------------------------|
    | $L$   | Number of impact categories            |
    | $R$   | Number of rows in the B-matrix         |

    See Also
    --------
    [`greengraph.math.matrix.calculate_impact_vector`][]

    Parameters
    ----------
    g_matrix : np.ndarray
        Inventory matrix $\mathbf{g}$ of the system.  
        $\text{dim}(\mathbf{g})=[R \times C]$
    Q : np.ndarray
        Characterization matrix $\mathbf{Q}$ of the system.  
        $\text{dim}(\mathbf{Q})=[L \times R]$

    Returns
    -------
    np.ndarray
        Impact matrix $\mathbf{h}$.  
        $\text{dim}(\mathbf{h})=[L \times C]$
    """

    h_matrix = xr.DataArray(
        data=Q.data @ g_matrix.data,
        dims=('rows', 'cols'),
        coords={
            'rows': Q.coords['rows'].values,
            'cols': g_matrix.coords['cols'].values,
        }
    )

    return h_matrix


# %%

from greengraph.importers.databases.inputoutput import useeio
from greengraph.importers.databases.generic import graph_system_from_input_output_matrices

dct = useeio.load_useeio_data_from_zenodo(version='2.0.1-411')
G = graph_system_from_input_output_matrices(
    name_system='useeio',
    assign_new_uuids=True,
    str_extension_nodes_uuid='name',
    str_production_nodes_uuid='name',
    str_indicator_nodes_uuid='name',
    matrix_convention='I-A',
    array_production=dct['A'].to_numpy(),
    array_extension=dct['B'].to_numpy(),
    array_indicator=dct['C'].to_numpy(),
    list_dicts_production_node_metadata=dct['dicts_A_metadata'],
    list_dicts_extension_node_metadata=dct['dicts_B_metadata'],
    list_dicts_indicator_node_metadata=dct['dicts_C_metadata'],
)

from greengraph.math.conversion import _generate_matrices_from_graph

matrices = _generate_matrices_from_graph(
    G=G,
    matrixformat='dense',
    A=True,
    B=True,
    Q=True,
    A_sort_attributes=None,
    B_sort_attributes=None,
    Q_sort_attributes=None
)

# %%

x = calculate_production_vector(
    A=matrices['A'],
    demand={[node for node, attr in G.nodes(data=True) if attr['type']=='production'][0]: 100}
)
g = calculate_inventory_vector(
    x=x,
    B=matrices['B']
)
h = calculate_impact_vector(
    g=g,
    Q=matrices['Q']
)