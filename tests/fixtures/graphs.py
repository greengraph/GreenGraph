
G = _generic_graph_system_from_matrices(
    name_system="Test System",
    convention="A",
    matrix_technosphere=A_P,
    matrix_biosphere=B_P,
    list_dicts_technosphere_node_metadata=A_P_metadata,
    list_dicts_biosphere_node_metadata=B_P_metadata,
)

# %%
from greengraph.math.conversion import _generate_matrices_from_graph

A, B = _generate_matrices_from_graph(
    G,
    technosphere_matrix_sorting_attributes=["system"],
    biosphere_matrix_sorting_attributes=["system"],
    dense=True
)