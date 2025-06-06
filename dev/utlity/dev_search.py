# %%

from greengraph.importers.databases.inputoutput import useeio
from greengraph.importers.databases.generic import graph_system_from_input_output_matrices
Guseeio = useeio.create_graph()
Guseeio.search(dict_search_attributes={'name': '1-NAPTHALENAMINE (OR) ALPHA-NAPHTHYLAMINE', 'system': 'useeio'})