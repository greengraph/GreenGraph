# %%
import pandas as pd
from pathlib import Path

path = Path('/Users/michaelweinold/data/concordance_ecoinvent_exiobase.xlsx')

df = pd.read_excel(
    path,
    sheet_name='Hybridized processes',
    header=0
)

# need to build concordance matrix and infer flows - and correct for double-counting!

