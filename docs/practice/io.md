# Working with Input-Output Data

```python
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
```