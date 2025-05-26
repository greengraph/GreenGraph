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

B = np.array([
     # 1  # 2  # 3 
    [0.0, 1.5, 2.5], # alpha
    [3.5, 4.5, 0.0], # beta
])

B_labeled = xr.DataArray(
    data=B,
    dims=('rows','cols'),
    coords={
        'rows': ['emission alpha', 'emission beta'],
        'cols': ['process 1', 'process 2', 'process 3']
    }
)

Q = np.array([
    [-11.1, -22.2]
])
Q_labeled = xr.DataArray(
    data=Q,
    dims=('rows', 'cols'),
    coords={
        'rows': ['indicator 1'],
        'cols': ['emission alpha', 'emission beta']
    }
)

x = calculate_production_vector(
    A=A_labeled,
    demand={
        'process 1': 1.0,
    }
)

g = calculate_inventory_vector(
    x=x,
    B=B_labeled,
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
    assert np.allclose(
        x.values,
        [
            1.0,
            0.3*1.0,
            0.3*0.2*1.0
        ]
    )
    return x

@pytest.mark.parametrize(
    "A, demand",
    [
        (A_labeled, {'incorrect process name': 1.0}),
        (A_labeled, {'process 1': 0.0}),
        ("not a numpy array", {'process 1': 3.0}),
    ]
)
def test_production_vector_expected_failures(A, demand):
    with pytest.raises((ValueError, TypeError)):
        calculate_production_vector(A=A, demand=demand)


def test_calculate_inventory_vector():
    x = test_calculate_production_vector()
    g = calculate_inventory_vector(
        x=x,
        B=B_labeled,
    )
    assert isinstance(g, xr.DataArray)
    assert g.dims == ('rows',)
    assert set(g.coords['rows'].values) == {'emission alpha', 'emission beta'}
    assert np.allclose(
        g.values,
        [
            (1.0*0.3*1.5)+(1.0*0.3*0.2*2.5),
            (1.0*3.5)+(1.0*0.3*4.5)
        ]
    )
    return g

def test_calculate_impact_vector():
    g = test_calculate_inventory_vector()
    h = calculate_impact_vector(
        g=g,
        Q=Q_labeled,
    )
    assert isinstance(h, xr.DataArray)
    assert h.dims == ('rows',)
    assert set(h.coords['rows'].values) == {'indicator 1'}
    assert np.allclose(
        h.values,
        [
            (-11.1*(((1.0*0.3*1.5)+(1.0*0.3*0.2*2.5))) + (-22.2*((1.0*3.5)+(1.0*0.3*4.5))))
        ]
    )