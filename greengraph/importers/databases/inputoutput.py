# %%
import pandas as pd
from pandas.api.types import is_numeric_dtype
from pathlib import Path
import zipfile

from greengraph import APP_CACHE_BASE_DIR
from greengraph.utility.download import _load_file_from_zenodo_with_caching
from greengraph.utility.log import logtimer
from greengraph.importers.databases.generic import graph_system_from_input_output_matrices
from greengraph.core import GreenMultiDiGraph

class useeio:
    """
    Class for loading and formatting the USEEIO dataset.

    > "US Environmentally-Extended Input-Output (USEEIO) models are combined economic-environmental models.
    > The models use data on inputs to and outputs from industries and their final consumption and value added in the form of input-output tables from the Bureau of Economic Analysis (BEA).
    > These tables are paired with environmental data on resource use and releases of pollutants from various public sources in the form of satellite tables,
    > as well as indicators of potential environmental and economic impact, using standard algorithms from input-output analysis."  

    [United States Environmental Protection Agency (EPA) description of the _US Environmentally-Extended Input-Output (USEEIO) Technical Content_](https://www.epa.gov/land-research/us-environmentally-extended-input-output-useeio-technical-content)
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
    def _load_useeio_data_from_zenodo(
        version: str
    ) -> dict:
        """
        Given a version string of the USEEIO dataset, downloads the corresponding data from the Zenodo repository
        and passes it to the `format_useeio_matrices` function to extract the matrices and metadata.

        Warning
        -------
        USEEIO data for a single version is ~50MB. The download may take some time [depending on your internet connection](https://en.wikipedia.org/wiki/IP_over_Avian_Carriers).

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
        path_excel_file = _load_file_from_zenodo_with_caching(
            name_file=f'USEEIOv{version}.xlsx',
            name_dir_cache='useeio',
            zenodo_record='15272306',
        )

        return useeio._format_useeio_matrices(path_useeio=path_excel_file['path_cached_file'])
    
    @staticmethod
    def _format_useeio_matrices(
        path_useeio: Path
    ) -> dict:
        r"""
        Given a path to a USEEIO Excel file, extracts the matrices and metadata from the file
        and returns the $\mathbf{A}, \mathbf{B}, \mathbf{C}$ matrices and metadata as lists of dictionaries.

        Warnings
        --------
        The $\mathbf{A}$ matrix of the USEEIO model contains some sign-errors (negative values, albeit of small magnitude).
        In the current implementation, these values are corrected by simply setting them to zero.
        This follows a recommendation from experts at [NREL](https://en.wikipedia.org/wiki/National_Renewable_Energy_Laboratory).

        References
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
            ).abs()
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
            df_A_metadata = pd.read_excel(
                io=path_useeio,
                sheet_name='commodities_meta',
                header=0,
                index_col=1,
                engine='openpyxl',
            )
            df_A_annual_production = pd.read_excel(
                io=path_useeio,
                sheet_name='x',
                header=0,
                index_col=0,
                engine='openpyxl',
            )
            df_C_metadata = pd.read_excel(
                io=path_useeio,
                sheet_name='indicators',
                header=0,
                index_col=1,
                engine='openpyxl',
            )
            df_B_metadata = pd.read_excel(
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
            df_B_metadata = df_B_metadata.rename(columns=columns_flow_metadata)   
            df_B_metadata = df_B_metadata[columns_flow_metadata.values()]
            dicts_B_metadata = df_B_metadata.to_dict(orient='records')

            columns_sector_metadata = {
                'Name': 'name',
                'Location': 'location',
                'Code': 'code',
                'Category': 'category',
            }
            df_A_metadata = df_A_metadata.rename(columns=columns_sector_metadata)
            df_A_metadata = df_A_metadata[columns_sector_metadata.values()]
            df_A_metadata['unit'] = 'USD'

            df_A_annual_production = df_A_annual_production.rename(columns={'x': 'annual production'})
            df_A_metadata = pd.merge(
                left=df_A_metadata,
                right=df_A_annual_production,
                how='left',
                left_index=True,
                right_index=True
            )

            dicts_A_metadata = df_A_metadata.to_dict(orient='records')

            columns_indicator_metadata = {
                'Name': 'name',
                'Code': 'code',
                'Unit': 'unit',
                'Group': 'group',
                'SimpleName': 'description'
            }
            df_C_metadata = df_C_metadata.rename(columns=columns_indicator_metadata)
            df_C_metadata = df_C_metadata[columns_indicator_metadata.values()]
            dicts_C_metadata = df_C_metadata.to_dict(orient='records')

        return {
            'A': df_A,
            'B': df_B,
            'C': df_C,
            'dicts_A_metadata': dicts_A_metadata,
            'dicts_B_metadata': dicts_B_metadata,
            'dicts_C_metadata': dicts_C_metadata
        }
    

    @staticmethod
    def create_graph(
        version: str = '2.0.1-411'
    ) -> GreenMultiDiGraph:
        r"""
        Creates a GreenMultiDiGraph from the USEEIO dataset for a given version.

        Parameters
        ----------
        version : str, optional
            The version of the USEEIO dataset to use. Must be one of the available versions.
            See [`greengraph.importers.databases.inputoutput.useeio.list_available_versions`][] for a list of available versions.
            Default is `2.0.1-411`.
        
        Returns
        -------
        GreenMultiDiGraph
            A GreenMultiDiGraph representing the USEEIO dataset for the given version.

        Raises
        ------
        ValueError
            If the version is not available.
        HTTPError
            If the request to download the USEEIO data fails.
        """
        dict_zenodo_data = useeio._load_useeio_data_from_zenodo(version=version)
        G = graph_system_from_input_output_matrices(
            name_system='useeio',
            assign_new_uuids=True,
            str_extension_nodes_uuid='name',
            str_production_nodes_uuid='name',
            str_indicator_nodes_uuid='name',
            matrix_convention='I-A',
            array_production=dict_zenodo_data['A'].to_numpy(),
            array_extension=dict_zenodo_data['B'].to_numpy(),
            array_indicator=dict_zenodo_data['C'].to_numpy(),
            list_dicts_production_node_metadata=dict_zenodo_data['dicts_A_metadata'],
            list_dicts_extension_node_metadata=dict_zenodo_data['dicts_B_metadata'],
            list_dicts_indicator_node_metadata=dict_zenodo_data['dicts_C_metadata'],
        )
        return G


class exiobase:
    """
    Class for loading and formatting the Exiobase dataset.

    > "EXIOBASE 3 provides a time series of environmentally extended multi-regional input-output (EE MRIO) tables
    > ranging from 1995 to a recent year for 44 countries (28 EU member plus 16 major economies) and five rest of the world regions.
    > EXIOBASE 3 builds upon the previous versions of EXIOBASE by using rectangular supply-use tables (SUT)
    > in a 163 industry by 200 products classification as the main building blocks.
    > The tables are provided in current, basic prices (Million EUR).

    [EXIOBASE 3 description on Zenodo](https://doi.org/10.5281/zenodo.3583070)
    """

    _available_versions_and_years = {
        '3.8.2': {
            'zenodo_record': '5589597',
            'available_years': [1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022],
        }
    }
    
    @staticmethod
    def list_available_versions() -> list[str]:
        """
        Lists the available versions of the Exiobase dataset.

        Returns
        -------
        list[str]
            A list of available versions of the Exiobase dataset.
        """
        return list(exiobase._available_versions_and_years.keys())
    
    @staticmethod
    def list_available_years(version: str) -> list[int]:
        """
        Lists the available years for a given version of the Exiobase dataset.

        Parameters
        ----------
        version : str
            The version of the Exiobase dataset to check. Must be one of the available versions.
            See [`greengraph.importers.databases.inputoutput.exiobase.list_available_versions`][] for a list of available versions.

        Returns
        -------
        list[int]
            A list of available years for the given version of the Exiobase dataset.

        Raises
        ------
        ValueError
            If the version is not available.
        """
        if version not in exiobase._available_versions_and_years:
            raise ValueError(f"Version {version} is not available.")
        
        return exiobase._available_versions_and_years[version]['available_years']
    
    @staticmethod
    def load_exiobase_data_from_zenodo(
        version: str,
        year: int,
        type: str
    ) -> dict:
        """
        Given a version string of the Exiobase dataset, downloads the corresponding data from the Zenodo repository
        and passes it to the [`greengraph.importers.databases.inputoutput.exiobase.format_exiobase_matrices`][] function to extract the matrices and metadata.

        Warning
        -------
        Exiobase data for a single version is ~700MB. The download may take some time [depending on your internet connection](https://en.wikipedia.org/wiki/IP_over_Avian_Carriers).

        See Also
        --------
        [EXIOBASE 3](https://doi.org/10.5281/zenodo.3583070) on Zenodo

        Parameters
        ----------
        version : str
            The version of Exiobase to use. Must be one of the available versions.
            See [`greengraph.importers.databases.inputoutput.exiobase.list_available_versions`][] for a list of available versions.
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
        if not isinstance(year, int):
            raise TypeError("year must be an integer.")
        if not isinstance(type, str):
            raise TypeError("type must be a string.")
        type = type.lower()
        if type not in ['ixi', 'pxp']:
            raise ValueError("type must be either 'ixi' or 'pxp'")
        if version not in exiobase._available_versions_and_years:
            raise ValueError(f"Version {version} is not available.")
        if year not in exiobase._available_versions_and_years[version]['available_years']:
            raise ValueError(f"Year {year} is not available for version {version}. Available years: {exiobase._available_versions_and_years[version]['available_years']}")
        
        dict_paths_download = _load_file_from_zenodo_with_caching(
            name_file=f"IOT_{year}_{type}.zip",
            name_dir_cache="useeio",
            zenodo_record=exiobase._available_versions_and_years[version]['zenodo_record'],
        )
        dict_exiobase_files = exiobase.unpack_exiobase_zip(
            path_zip=dict_paths_download['path_cached_file'],
        )
        return exiobase.format_exiobase_matrices(
            path_A=dict_exiobase_files['path_A'],
            path_S=dict_exiobase_files['path_S'],
            path_S_metadata=dict_exiobase_files['path_S_metadata'],
            path_x=dict_exiobase_files['path_x'],
        )

    
    @staticmethod
    def unpack_exiobase_zip(
        path_zip: Path,
    ) -> dict:
        """
        Unpacks the Exiobase zip file and returns the paths to the relevant files.

        Parameters
        ----------
        path_zip : Path
            Path to the Exiobase zip file. This can be a local file path or a BytesIO object.

        Returns
        -------
        dict
            A dictionary containing the paths to the relevant files.
        """
        with logtimer(f"unpacking Exiobase zip file."):
            
            with zipfile.ZipFile(path_zip, 'r') as zip:

                path_file_A = [name for name in zip.namelist() if name.endswith('A.txt')]
                if len(path_file_A) == 0:
                    raise ValueError("No 'A.txt' found in zip file.")
                elif len(path_file_A) > 1:
                    raise ValueError("Multiple 'A.txt' found in zip file")
                top_level_dir = path_file_A[0].split('/')[0]

                file_A = zip.extract(
                    member=f"{top_level_dir}/A.txt",
                    path=APP_CACHE_BASE_DIR / 'exiobase'
                )
                file_S = zip.extract(
                    member=f"{top_level_dir}/satellite/S.txt",
                    path=APP_CACHE_BASE_DIR  / 'exiobase'
                )
                file_S_metadata = zip.extract(
                    member=f"{top_level_dir}/satellite/unit.txt",
                    path=APP_CACHE_BASE_DIR  / 'exiobase'
                )      
                file_s = zip.extract(
                    member=f"{top_level_dir}/x.txt",       
                    path=APP_CACHE_BASE_DIR  / 'exiobase'
                )   

        return {
            'path_A': Path(file_A),
            'path_S': Path(file_S),
            'path_S_metadata': Path(file_S_metadata),
            'path_x': Path(file_s),
        }

    @staticmethod
    def format_exiobase_matrices(
        path_A: Path,
        path_S: Path,
        path_S_metadata: Path,
        path_x: Path
    ) -> dict:
        r"""
        Given a path to the relevant Exiobase txt-files, extracts the matrices and metadata from the files
        and returns the $\mathbf{A}$ and $\mathbf{B}$ matrices and metadata as lists of dictionaries.

        References
        ----------
        - Stadler, Konstantin, et al.
        "EXIOBASE 3: Developing a time series of detailed environmentally extended multi-regional input-output tables."
        _Journal of Industrial Ecology_ 22.3 (2018): 502-515.
        doi:[10.1111/jiec.12715](https://doi.org/10.1111/jiec.12715)
        - [EXIOBASE 3 datasets on Zenodo](https://doi.org/10.5281/zenodo.3583070)

        Parameters
        ----------
        path_A : Path
            Path to the Exiobase A matrix file. This can be a local file path or a BytesIO object.  
            Usually located at `IOT_{year}_{type}/A.txt` in the Exiobase zip file.
        path_S : Path
            Path to the Exiobase S matrix file. This can be a local file path or a BytesIO object.  
            Usually located at `IOT_{year}_{type}/satellite/S.txt` in the Exiobase zip file.
        path_S_metadata : Path
            Path to the Exiobase S metadata file. This can be a local file path or a BytesIO object.  
            Usually located at `IOT_{year}_{type}/satellite/unit.txt` in the Exiobase zip file.

        Returns
        -------
        dict
            A dictionary containing the Exiobase data matrices and metadata.

            | Key                 | Description                                                                               |
            |---------------------|-------------------------------------------------------------------------------------------|
            | A                   | $\mathbf{A}$ matrix                                                                       |
            | S                   | $\mathbf{B}$ matrix                                                                       |
            | sector_metadata     | Metadata for the sectors in the model (`name`, `location`, `unit`)                        |
            | flow_metadata       | Metadata for the flows in the model (`name`, `unit`)                                      |
        """
        with logtimer(f"extracting Exiobase data from txt files."):
            df_A = pd.read_csv(
                path_A,
                delimiter='\t',
                skiprows=3,
                header=None
            )
            df_A_metadata = df_A.iloc[:, [0, 1]].copy()
            df_A.drop(columns=[0, 1], inplace=True)
            df_A_metadata.columns = ['location', 'name']
            df_A_metadata['unit'] = 'USD'

            df_S = pd.read_csv(
                path_S,
                delimiter='\t',
                skiprows=3,
                header=None
            )
            df_S.drop(columns=[0], inplace=True)
            df_S_metadata = pd.read_csv(
                path_S_metadata,
                delimiter='\t',
                skiprows=1,
                header=None
            )
            df_S_metadata.columns = ['name', 'unit']

            df_x = pd.read_csv(
                path_x,
                delimiter='\t',
                header=0
            )
            df_x['annual production'] = df_x['indout'] * 1E6  # convert from million EUR to EUR
            df_x.drop(columns=['indout'], inplace=True)
            df_A_metadata = pd.merge(
                left=df_A_metadata,
                right=df_x,
                how='left',
                left_on=['location', 'name'],
                right_on=['region', 'sector']
            )
            del df_x

        for df in [df_A, df_S]:
            if all(is_numeric_dtype(df[col]) for col in df.columns) == False:
                raise TypeError("Warning! Not all extracted elements are numeric!")
        if df_A.shape[0] != df_A.shape[1]:
            raise ValueError("Warning! Technosphere matrix must be square.")
        if df_A.shape[0] != df_A_metadata.shape[0]:
            raise ValueError("Warning! Matrix technosphere shape does not match metadata length.")
        if df_S.shape[0] != df_S_metadata.shape[0]:
            raise ValueError("Warning! Matrix biosphere shape does not match metadata length.")

        return {
            'A': df_A,
            'S': df_S,
            'dicts_A_metadata': df_A_metadata.to_dict(orient='records'),
            'dicts_S_metadata': df_S_metadata.to_dict(orient='records'),
        }
    
    @staticmethod
    def create_graph(
        version: str = '3.8.2',
        year: int = 2021,
        type: str = 'ixi'
    ) -> GreenMultiDiGraph:
        r"""
        Creates a GreenMultiDiGraph from the Exiobase dataset for a given version and year.

        Parameters
        ----------
        version : str, optional
            The version of the Exiobase dataset to use. Must be one of the available versions.
            See [`greengraph.importers.databases.inputoutput.exiobase.list_available_versions`][] for a list of available versions.
            Default is `3.8.2`.
        year : int, optional
            The year of the Exiobase dataset to use. Must be one of the available years for the given version.
            See [`greengraph.importers.databases.inputoutput.exiobase.list_available_years`][] for a list of available years.
            Default is `2021`.
        type : str, optional
            The type of Exiobase dataset to use. Must be either 'ixi' or 'pxp'.
            Default is 'ixi'.

        Returns
        -------
        GreenMultiDiGraph
            A GreenMultiDiGraph representing the Exiobase dataset for the given version and year.

        Raises
        ------
        ValueError
            If the version or year is not available.
        HTTPError
            If the request to download the Exiobase data fails.
        """
        dict_zenodo_data = exiobase.load_exiobase_data_from_zenodo(
            version=version,
            year=year,
            type=type,
        )
        G = graph_system_from_input_output_matrices(
            name_system='exiobase',
            assign_new_uuids=True,
            str_production_nodes_uuid=None,
            str_extension_nodes_uuid=None,
            str_indicator_nodes_uuid=None,
            matrix_convention='I-A',
            array_production=dict_zenodo_data['A'].to_numpy(),
            array_extension=dict_zenodo_data['S'].to_numpy(),
            array_indicator=None,
            list_dicts_production_node_metadata=dict_zenodo_data['dicts_A_metadata'],
            list_dicts_extension_node_metadata=dict_zenodo_data['dicts_S_metadata'],
            list_dicts_indicator_node_metadata=None,
        )
        return G