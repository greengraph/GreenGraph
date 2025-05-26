# %%

import pytest
import xarray as xr
import numpy as np

from greengraph.math.matrix import (
    calculate_production_vector,
    calculate_inventory_vector,
    calculate_impact_vector,
    calculate_inventory_matrix,
    calculate_impact_matrix,
)

A = np.array([
     # 1  # 2  # 3 
    [0.0, 0.0, 0.0], # 1
    [0.3, 0.0, 0.0], # 2
    [0.0, 0.2, 0.0], # 3
])

A_labeled = xr.DataArray(
    data=A,
    dims=('rows','cols'),
    coords={
        'rows': ['process 1', 'process 2', 'process 3'],
        'cols': ['process 1', 'process 2', 'process 3']
    }
)

B_S = np.array([
    [3.5, 2.1, 4.0, 7.1],
    [0.8, 1.5, 0.0, 3.6]
])

Q_S = np.array([
    [-2.0, -13.2]
])

x = calculate_production_vector(
    A=A_labeled,
    demand={
        'process 1': 1.0,
    }
)

# %%

def test_calculate_production_vector():
    x = calculate_production_vector(
        A=A_labeled,
        demand={
            'process 1': 1.0,
        }
    )
    assert isinstance(x, xr.DataArray)
    assert x.dims == ('rows',)
    assert set(x.coords['rows'].values) == {'process 1', 'process 2', 'process 3'}
    assert np.allclose(x.values, [1.0, 0.3*1.0, 0.3*0.2*1.0])