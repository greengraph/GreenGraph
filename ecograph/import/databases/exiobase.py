import networkx as nx
import pandas as pd
import numpy as np
import xarray as xr
import logging


def load_exiobase_from_zenodo(
    'version': str,
    'format': str,
) -> None:
    """_summary_

    _extended_summary_

    Warnings
    --------
    Downloads are ~500MB per EXIOBASE version.

    Raises
    ------
    ValueError
        _description_
    """
    if 'format' not in ['pxp', 'ixi']:
        raise ValueError("format must be 'pxp' (product-by-product) or 'ixi (industry-by-industry)'")

def read_exiobase() -> xr.DataArray:
    """_summary_

    _extended_summary_

    See Also
    --------
    - [EXIOBASE 3 on Zenodo](https://doi.org/10.5281/zenodo.3583070)
    - [Section "Terminology" in the `pymrio` Documentation](https://pymrio.readthedocs.io/en/latest/terminology.html)
    - [Miller & Blair (3rd Edition, 2022)](https://doi.org/10.1017/9781108676212)


    Returns
    -------
    xr.DataArray
        _description_
    """

# %%

import pandas as pd

df_data = pd.read_csv(
    '/Users/michaelweinold/data/IOT_2022_ixi/A.txt',
    sep='\t',
    skiprows=3,
    usecols=range(3, pd.read_csv('/Users/michaelweinold/data/IOT_2022_ixi/A.txt', sep='\t', nrows=1).shape[1]),
    header=None,
    index_col=None,
)

df_indices = pd.read_csv(
    '/Users/michaelweinold/data/IOT_2022_ixi/A.txt',
    skiprows=3,
    usecols=[0, 1],
    sep='\t',
    header=None
)

row_index = pd.MultiIndex.from_arrays([df_indices[0], df_indices[1]])

df_data.index = row_index
