# %%

from greengraph.importers.databases.inputoutput import useeio
from greengraph.importers.databases.generic import graph_system_from_input_output_matrices
Guseeio = useeio.create_graph()

# %%

results = Guseeio.hashsearch(
    dict_search_attributes={'system': 'useeio'},
    enforce_unique_results=False
)

result = Guseeio.hashsearch(
    dict_search_attributes={'name': 'Other durable goods merchant wholesalers'},
    dict_filter_attributes={'type': 'production'}
)