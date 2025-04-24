r"""
> "US Environmentally-Extended Input-Output (USEEIO) models are combined economic-environmental models.
> The models use data on inputs to and outputs from industries and their final consumption and value added in the form of input-output tables from the Bureau of Economic Analysis (BEA).
> These tables are paired with environmental data on resource use and releases of pollutants from various public sources in the form of satellite tables,
> as well as indicators of potential environmental and economic impact, using standard algorithms from input-output analysis."  

[United States Environmental Protection Agency (EPA) description of the _US Environmentally-Extended Input-Output (USEEIO) Technical Content_](https://www.epa.gov/land-research/us-environmentally-extended-input-output-useeio-technical-content)
"""

# %%

import pandas as pd
import numpy as np
from pathlib import Path

path_useeio = Path('/Users/michaelweinold/data/USEEIOv2.0.1-411.xlsx')



def load_useeio() -> pd.DataFrame:
    r"""

    Load the US Environmentally-Extended Input-Output (USEEIO) model matrices and metadata.

    See Also
    --------
    https://doi.org/10.1016/j.jclepro.2017.04.150
    https://catalog.data.gov/dataset/useeio-v1-1-matrices
    https://catalog.data.gov/dataset/useeio-v2-0-1-411

    https://pasteur.epa.gov/uploads/10.23719/1524311/USEEIOv2.0.1-411.xlsx
    """
    df_A = pd.read_excel(
        io=path_useeio,
        sheet_name='A',
        header=0,
        index_col=0,
        engine='openpyxl',
    )
    df_B = pd.read_excel(
        io=path_useeio,
        sheet_name='B',
        header=0,
        index_col=0,
        engine='openpyxl',
    )
    df_C = pd.read_excel(
        io=path_useeio,
        sheet_name='C',
        header=0,
        index_col=0,
        engine='openpyxl',
    )
    df_sector_metadata = pd.read_excel(
        io=path_useeio,
        sheet_name='commodities_meta',
        header=0,
        index_col=1,
        engine='openpyxl',
    )
    df_indicator_metadata = pd.read_excel(
        io=path_useeio,
        sheet_name='indicators',
        header=0,
        index_col=1,
        engine='openpyxl',
    )
    df_flow_metadata = pd.read_excel(
        io=path_useeio,
        sheet_name='flows',
        header=0,
        index_col=1,
        engine='openpyxl',
    )

    columns_flow_metadata = {
            'Flowable': 'name',
            'Context': 'context',
            'Unit': 'unit'
        }
    df_flow_metadata = df_flow_metadata.rename(columns=columns_flow_metadata)   
    df_flow_metadata = df_flow_metadata[columns_flow_metadata.values()]
    dict_flow_metadata = df_flow_metadata.to_dict(orient='records')

    columns_sector_metadata = {
            'Name': 'name',
            'Location': 'location',
        }
    df_sector_metadata = df_sector_metadata.rename(columns=columns_sector_metadata)
    df_sector_metadata = df_sector_metadata[columns_sector_metadata.values()]
    dict_sector_metadata = df_sector_metadata.to_dict(orient='records')
    for sector in dict_sector_metadata:
        sector['unit'] = 'USD'

    columns_indicator_metadata = {
        'Name': 'name',
        'Code': 'code',
        'Unit': 'unit',
        'Group': 'group',
        'SimpleName': 'description'
    }
    df_indicator_metadata = df_indicator_metadata.rename(columns=columns_indicator_metadata)
    df_indicator_metadata = df_indicator_metadata[columns_indicator_metadata.values()]
    dict_indicator_metadata = df_indicator_metadata.to_dict(orient='records')

    return {
        'A': df_A,
        'B': df_B,
        'C': df_C,
        'flow_metadata': dict_flow_metadata,
        'sector_metadata': dict_sector_metadata,
        'indicator_metadata': dict_indicator_metadata
    }