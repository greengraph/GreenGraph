# %%
from pathlib import Path

Gexio = exiobase.create_graph(
    version='3.8.2',
    year=2021,
    type='pxp'
)

import pickle
with open('/Users/michaelweinold/github/GreenGraph/dev/Gexio.pkl', 'wb') as f:
    pickle.dump(Gexio, f)