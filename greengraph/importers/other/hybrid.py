# %%

import pandas as pd

from greengraph.importers.databases.inputoutput import exiobase
from greengraph.utility.data import (
    _dict_to_tuple,
    _create_dynamic_lookup_dictionary
)

# %%

df = pd.read_excel(
    "/Users/michaelweinold/github/pylcaio/src/Data/mappings/filters.xlsx",
    sheet_name="Hybridized processes",
    header=0,
)

# %%

Gexio = exiobase.create_graph()

# %%

dict_lookup = _create_dynamic_lookup_dictionary(
    G=Gexio,
    node_type='production',
    list_attributes=['name', 'location']
)