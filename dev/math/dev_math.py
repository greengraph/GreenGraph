# %%

from greengraph.importers.databases.inputoutput import useeio
from greengraph.importers.databases.generic import graph_system_from_input_output_matrices

Guseeio = useeio.create_graph()

Museeio = Guseeio.generate_matrices(
    matrixformat='dense',
    generate_A=True,
    generate_B=True,
    generate_Q=False
)

Museeio.lca(demand={Guseeio.get_random_node(type='production'): 1.0}, format_return='dataframe')

