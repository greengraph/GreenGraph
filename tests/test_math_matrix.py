# %%

import pytest

from tests.fixtures.matrices import (
    A_S,
)

from greengraph.math.matrix import (
    calculate_production_vector,
    calculate_inventory_vector,
    calculate_impact_vector,
    calculate_inventory_matrix,
    calculate_impact_matrix,
)

import xarray as xr
import uuid
import numpy as np

A = xr.DataArray(
    data=A_S,
    dims=('rows','cols'),
    coords={
        'rows': [str(uuid.uuid4()) for _ in range(A_S.shape[0])],
        'cols': [str(uuid.uuid4()) for _ in range(A_S.shape[0])]
    }
)

B_S = np.array([
    [3.5, 2.1, 4.0, 7.1],
    [0.8, 1.5, 0.0, 3.6]
])

Q_S = np.array([
    [-2.0, -13.2]
])

# %%

x = calculate_production_vector(
    A=A,
    demand={
        A.coords['rows'][0].item(): 1.0,
        A.coords['rows'][1].item(): 2.0,
    }
)

# %%

B = xr.DataArray(
    data=B_S,
    dims=('rows','cols'),
    coords={
        'rows': ['sat1', 'sat2'],
        'cols': A['rows'].values
    }
)

g = calculate_inventory_vector(
    x=x,
    B=B
)


Q = xr.DataArray(
    data=Q_S,
    dims=('rows','cols'),
    coords={
        'rows': ['impact1'],
        'cols': B['rows'].values
    }
)

h = calculate_impact_vector(
    g=g,
    Q=Q
)


# %%

g_matrix = calculate_inventory_matrix(
    x=x,
    inventory_split={
        'system1': [A.coords['rows'][0].item(), A.coords['rows'][1].item()],
        'system2': [A.coords['rows'][2].item(), A.coords['rows'][3].item()]
    },
    B=B
)


h_matrix = calculate_impact_matrix(
    g_matrix=g_matrix,
    Q=Q
)