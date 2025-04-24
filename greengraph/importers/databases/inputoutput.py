r"""
> "US Environmentally-Extended Input-Output (USEEIO) models are combined economic-environmental models.
> The models use data on inputs to and outputs from industries and their final consumption and value added in the form of input-output tables from the Bureau of Economic Analysis (BEA).
> These tables are paired with environmental data on resource use and releases of pollutants from various public sources in the form of satellite tables,
> as well as indicators of potential environmental and economic impact, using standard algorithms from input-output analysis."  

[United States Environmental Protection Agency (EPA) description of the _US Environmentally-Extended Input-Output (USEEIO) Technical Content_](https://www.epa.gov/land-research/us-environmentally-extended-input-output-useeio-technical-content)
"""

import pandas as pd
import requests
from pathlib import Path
from io import BytesIO
from greengraph.utility.logging import logtimer


class useeio:
    """
    Class for loading and formatting the USEEIO dataset.
    """

    _available_versions = ['2.0.1-411']
    
    @staticmethod
    def list_available_versions() -> list[str]:
        """
        Lists the available versions of the USEEIO dataset.

        Returns
        -------
        list[str]
            A list of available versions of the USEEIO dataset.
        """
        return useeio._available_versions
    
    @staticmethod
    def load_useeio_data_from_zenodo(
        version: str
    ) -> dict:
        """
        Given a version string of the USEEIO dataset, downloads the corresponding data from the Zenodo repository
        and passes it to the `format_useeio_matrices` function to extract the matrices and metadata.

        Warning
        -------
        USEEIO data for a single version is ~50MB. The download may take some time depending on your internet connection.

        See Also
        --------
        [United States Environmentally-Extended Input-Output (USEEIO) Datasets](https://doi.org/10.5281/zenodo.15272305) on Zenodo

        Parameters
        ----------
        version : str
            The version of the USEEIO data to load. Must be one of the available versions.
            See [`greengraph.importers.databases.inputoutput.useeio.list_available_versions`][] for a list of available versions.
        
        Returns
        -------
        dict
            A dictionary containing the USEEIO data matrices and metadata.
            See [`greengraph.importers.databases.inputoutput.useeio.format_useeio_matrices`][] for details on the structure of the returned dictionary.

        Raises
        ------
        HTTPError
            If the request to download the USEEIO data fails.
        """
        with logtimer(f"downloading USEEIO data (v{version}) from Zenodo."):
            download = requests.get(f"https://zenodo.org/records/15272306/files/USEEIOv{version}.xlsx?download=1")
            download.raise_for_status()
            excel_file = BytesIO(download.content)
        return useeio.format_useeio_matrices(path_useeio=excel_file)
        
    @staticmethod
    def format_useeio_matrices(
        path_useeio: Path
    ) -> pd.DataFrame:
        r"""
        Given a path to a USEEIO Excel file, function extracts the matrices and metadata from the file
        and returns the $\mathbf{A}, \mathbf{B}, \mathbf{C}$ matrices and metadata as lists of dictionaries.

        See Also
        --------
        - Yang, Yi, et al.
        "USEEIO: A new and transparent United States environmentally-extended input-output model."
        _Journal of Cleaner Production_ 158 (2017): 308-318.
        doi:[10.1016/j.jclepro.2017.04.150](https://doi.org/10.1016/j.jclepro.2017.04.150)
        - ["Model and Model Component Formats" (description of matrices, etc.)](https://github.com/USEPA/useeior/blob/v1.0.0/format_specs/Model.md)

        Parameters
        ----------
        path_useeio : Path
            Path to the USEEIO Excel file. This can be a local file path or a BytesIO object.

        Returns
        -------
        dict
            A dictionary containing the USEEIO data matrices and metadata.  

            | Key                 | Description                                                                               |
            |---------------------|-------------------------------------------------------------------------------------------|
            | A                   | $\mathbf{A}$ matrix                                                                       |
            | B                   | $\mathbf{B}$ matrix                                                                       |
            | C                   | $\mathbf{C}$ matrix                                                                       |
            | sector_metadata     | Metadata for the sectors in the model (`name`, `location`, `unit`)                        |
            | flow_metadata       | Metadata for the flows in the model (`name`, `context`, `unit`)                           |
            | indicator_metadata  | Metadata for the indicators in the model (`name`, `code`, `unit`, `group`, `description`) |
        """
        with logtimer(f"extracting USEEIO data from Excel file."):
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

        with logtimer(f"modifying USEEIO data."):
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
            'sector_metadata': dict_sector_metadata,
            'flow_metadata': dict_flow_metadata,
            'indicator_metadata': dict_indicator_metadata
        }