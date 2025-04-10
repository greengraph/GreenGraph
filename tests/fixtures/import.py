# %%
import numpy as np
from ecograph

A_P = np.array([
    [1.0, 0.0, 0.0, 5.7],
    [2.0, 1.0, 7.2, 2.2],
    [9.2, 3.3, 1.0, 0.0],
    [0.4, 1.0, 1.2, 1.0]
])

A_P_metadata = [
    {"name": "Product 1", "unit": "kg", "location": "CH", "code": "123abc"},
    {"name": "Product 2", "unit": "kg", "location": "DE", "code": "456def"},
    {"name": "Product 3", "unit": "kg", "location": "FR", "code": "789ghi"},
    {"name": "Product 4", "unit": "kg", "location": "IT", "code": "012jkl"}
]

A_S = np.array([
    [0.1, 0.3, 0.1],
    [0.4, 0.2, 0.6],
    [0.2, 0.7, 0.3]
])

A_S_metadata = [
    {"name": "Sector A", "unit": "USD", "location": "CH",},
    {"name": "Sector B", "unit": "USD", "location": "DE",},
    {"name": "Sector C", "unit": "USD", "location": "FR",}
]

B_P = np.array([
    [3.5, 2.1, 4.0, 1.2],
    [0.8, 1.5, 2.3, 3.7]
])

B_P_metadata = [
    {"name": "Emission 1", "unit": "kg(CO2 eq.)", "compartment": "air"},
    {"name": "Emission 2", "unit": "kg(CO2 eq.)", "compartment": "air"},
]

B_S = np.array([[1.2, 3.4, 5.6]])

B_S_metadata = [
    {"name": "Emission 3", "unit": "kg(CO2 eq.)", "compartment": "air"},
]