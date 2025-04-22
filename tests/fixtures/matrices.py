# %%
import numpy as np
import networkx as nx

A_P = np.array([
    [1.0, 0.0, 0.0],
    [2.0, 1.0, 0.2],
    [0.0, 3.3, 1.0],
])

A_P_metadata = [
    {"name": "Product 1", "unit": "kg", "location": "CH", "code": "123abc"},
    {"name": "Product 2", "unit": "kg", "location": "CH", "code": "456def"},
    {"name": "Product 3", "unit": "kg", "location": "CH", "code": "789ghi"},
]

A_S = np.array([
    [0.2008, 0.0000, 0.0011, 0.0338],
    [0.0010, 0.0658, 0.0035, 0.0219],
    [0.0034, 0.0002, 0.0012, 0.0021],
    [0.1247, 0.0684, 0.1801, 0.2319]
])

A_S_metadata = [
    {"name": "Sector A", "unit": "CHF", "location": "CH",},
    {"name": "Sector B", "unit": "CHF", "location": "CH",},
    {"name": "Sector C", "unit": "CHF", "location": "CH",},
    {"name": "Sector D", "unit": "CHF", "location": "CH",}
]

B_P = np.array([
    [3.5, 2.1, 4.0],
    [0.8, 1.5, 0.0]
])

B_P_metadata = [
    {"name": "Emission 1 (Biosphere)", "unit": "kg(CO2 eq.)", "compartment": "air"},
    {"name": "Emission 2 (Biosphere)", "unit": "kg(CO2 eq.)", "compartment": "air"},
]

B_S = np.array([[1.2, 3.4, 5.6]])

B_S_metadata = [
    {"name": "Emission 3 (Satellite)", "unit": "kg(CO2 eq.)"},
]

H = np.array([
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0]
])