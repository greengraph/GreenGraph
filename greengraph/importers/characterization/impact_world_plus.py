# %%

import pandas as pd
import networkx as nx
from greengraph.utility.logging import logtimer


def _load_iwp_data(
    version_iwp: str,
    type_iwp: str,
    database: str,
    version_database: str,
) -> pd.DataFrame:
    """
    Given a valid version of IMPACT World+ and the Ecoinvent database,
    returns a dataframe of the Excel sheets containing characterization factors.

    | Links are of the form...                                                                                         |
    |------------------------------------------------------------------------------------------------------------------|
    | `https://zenodo.org/records/14041258/files/impact_world_plus_2.1_expert_version_ecoinvent_v3.10.xlsx?download=1` |
    | `https://zenodo.org/records/14041258/files/impact_world_plus_2.1_expert_version_exiobase.xlsx?download=1`        |

    Notes
    -----
    Available versions:

    | IMPACT World+                                   | `ecoinvent`                  | `exiobase` |
    | ----------------------------------------------- | ---------------------------- | ---------- |
    | `2.0.1` (`footprint_version`, `expert_version`) | `3.8`, `3.9`                 | `None`     |
    | `2.1` (`footprint_version`, `expert_version`)   | `3.8`, `3.9`, `3.10`, `3.11` | `None`     |

    See Also
    --------
    - [IMPACT World Plus Data on Zenodo](https://doi.org/10.5281/zenodo.1488368)
    - [IMPACT World Plus Website](https://www.impactworldplus.org)
    - Bulle, Cécile, et al. "IMPACT World+: a globally regionalized life cycle impact assessment method."
      _The International Journal of Life Cycle Assessment_ 24 (2019): 1653-1674.
      doi: [10.1007/s11367-019-01583-0](https://doi.org/10.1007/s11367-019-01583-0)

    Example
    -------
    ```python
    >>> df = _load_impact_world_plus_data(
    ...     version_iwp='2.1',
    ...     type_iwp='expert_version',
    ...     database='ecoinvent',
    ...     version_database='3.10'
    ... )
    ```

    Parameters
    ----------
    version_iwp : str
        Version of IMPACT World+
    type_iwp : str
        Type of IMPACT World+ (e.g., `footprint_version`, `expert_version`)
    database : str
        Database name (e.g., `ecoinvent`, `exiobase`)
    version_database : str
        Version of the database (e.g., `3.8`, `3.9`, `3.10`, `3.11`)

    Returns
    -------
    pd.DataFrame
        DataFrame containing characterization factors for the specified versions of IMPACT World+ and Ecoinvent.
    """

    iwp_version_id = {
        '2.0.1': '8200703',
        '2.1': '14041258'
    }

    if version_database == None:
        version_database = ""
    else:
        version_database = version_database.replace('.', '')
        version_database = f"_v{version_database}"
    
    path_download = f"https://zenodo.org/records/{iwp_version_id[version_iwp]}/files/impact_world_plus_{version_iwp}_{type_iwp}_{database}{version_database}.xlsx?download=1"

    with logtimer(f"downloading IMPACT World+ data ({database.capitalize()}) from Zenodo."):
        df = pd.read_excel(
            io=path_download,
            sheet_name='Sheet1',
            header=0,
            index_col=0,
            engine='openpyxl',
        )
    return df


def _extract_labels_from_exiobase_index(index_string) -> pd.Series:
    """
    Given an index string from the Impact World Plus Exiobase characterization dataframe,
    extracts the category and unit.

    Notes
    -----
    Index strings are of the form:

    ```python
    Water availability, human health (DALY)
    Climate change, long term (kg CO2 eq (long))
    ```

    Warnings
    -------
    The function assumes:

    - The first `(` indicates the start of the unit.
    - The last `)` indicates the end of the unit.
    - The unit is always in parentheses at the end of the string.
    
    Example
    -------
    ```python
    >>> index_string = "Climate change, long term (kg CO2 eq (long))"
    >>> _extract_labels_from_exiobase_index(index_string)
    ```
    returns a Pandas Series of the kind:

    |                                                  | Category                  | Unit             |
    |--------------------------------------------------|---------------------------|------------------|
    | **Climate change, long term (kg CO2 eq (long))** | Climate change, long term | kg CO2 eq (long) | 

    Parameters
    ----------
    index_string : str
        The index string to process.

    Returns
    -------
    pd.Series
        A pandas Series containing the category and unit.
        If the unit is not found, the unit will be None.
    """
    try:
        idx_first_open_bracket = index_string.find('(')
        idx_last_closed_bracket = index_string.rfind(')')
        idx_last_symbol = len(index_string.rstrip()) - 1

        if idx_first_open_bracket != -1 and idx_last_closed_bracket == idx_last_symbol and idx_first_open_bracket < idx_last_closed_bracket:
            category = index_string[:idx_first_open_bracket].strip()
            unit = index_string[idx_first_open_bracket + 1 : idx_last_closed_bracket]
            return pd.Series([category, unit], index=['Category', 'Unit'])
        else:
            return pd.Series([index_string.strip(), None], index=['Category', 'Unit'])

    except Exception as e:
        print(f"Error processing string '{index_string}': {e}")
        return pd.Series([index_string.strip(), None], index=['Category', 'Unit'])


def generate_iwp_characterization_matrix_ecoinvent(
    type_iwp: str,
    version_iwp: str,
    version_ecoinvent: str,
) -> pd.DataFrame:
    r"""
    Given a valid version and type of the IMPACT World+ method for life cycle impact assessment (LCIA)
    and the Ecoinvent database, returns a dataframe of the characterization matrix $\mathbf{Q}$.

    $$
    \mathbf{Q} = [Y \times R]
    $$

    where

    | Symbol | Description                                                                 |
    |--------|-----------------------------------------------------------------------------|
    | $Y$    | Number of individual impact assessment methods in the IMPACT World+ method. |
    | $R$    | Biosphere flows in the Ecoinvent biosphere database.                        |

    Notes
    -----
    Available versions:

    | IWP Version | IWP Type                              | Ecoinvent Version            | Exiobase Version |
    |-------------|---------------------------------------|------------------------------|------------------|
    | `2.0.1`     | `footprint_version`, `expert_version` | `3.8`, `3.9`                 | `None` (=v3)     |
    | `2.1`       | `footprint_version`, `expert_version` | `3.8`, `3.9`, `3.10`, `3.11` | `None` (=v3)     |

    See Also
    --------
    - Characterization Matrix $\mathbf{Q}$
        - Eqn.(8.26) in [Heijungs & Suh (2001)](https://doi.org/10.1007/978-94-015-9900-9), but see also ⚠️:
        - Eqn.(8.26) in [Errata of Heijungs & Suh (2001)](https://web.archive.org/web/20230505051343/https://personal.vu.nl/r.heijungs/computational/The%20computational%20structure%20of%20LCA%20-%20Errata.pdf)
    - IMPACT World Plus Method
        - [IMPACT World Plus Data on Zenodo](https://doi.org/10.5281/zenodo.1488368)
        - [IMPACT World Plus Website](https://www.impactworldplus.org)
        - Bulle, Cécile, et al. "IMPACT World+: a globally regionalized life cycle impact assessment method."
        _The International Journal of Life Cycle Assessment_ 24 (2019): 1653-1674.
        doi: [10.1007/s11367-019-01583-0](https://doi.org/10.1007/s11367-019-01583-0)

    Parameters
    ----------
    type_iwp : str
        Type of IMPACT World+ method  
        (e.g., `footprint_version`, `expert_version`)
    version_iwp : str
        Version of IMPACT World+  
        (e.g., `2.0.1`, `2.1`)
    type_iwp : str
        Type of IMPACT World+  
        (e.g., `footprint_version`, `expert_version`)
    version_ecoinvent : str
        Version of Ecoinvent  
        (e.g., `3.8`, `3.9`, `3.10`, `3.11`)

    Returns
    -------
    pd.DataFrame
        Characterization matrix $\mathbf{Q}$ for the specified version of IMPACT World+ and Ecionvent.
    """
    df = _load_iwp_data(
        version_iwp=version_iwp,
        type_iwp=type_iwp,
        database='ecoinvent',
        version_database=version_ecoinvent
    )
    """
    | Impact category           | Compartment | Sub-compartment | CF unit          | Elem flow name | CF value | (...) |
    |---------------------------|-------------|-----------------|------------------|----------------|----------|-------|
    | Climate change, long term | air         | unspecified     | kg CO2 eq (long) | Carbon dioxide | 1.0      | (...) |
    | Climate change, long term | air         | indoor          | kg CO2 eq (long) | Carbon dioxide | 10.1     | (...) |
    | Climate change, long term | air         | unspecified     | kg CO2 eq (long) | Methane        | 1.0      | (...) |
    | Climate change, long term | air         | indoor          | kg CO2 eq (long) | Methane        | 10.1     | (...) |
    """

    df_pivot = df.pivot(
        index=['Impact category', 'Compartment', 'Sub-compartment', 'CF unit'],
        columns='Elem flow name',
        values='CF value'
    ).reset_index()
    df_pivot.set_index(['Impact category', 'Compartment', 'Sub-compartment', 'CF unit'], inplace=True)
    df_pivot = df_pivot.fillna(0.0)
    """
    |                           |                  |     |             | Carbon dioxide | Methane       | (...) |
    |---------------------------|------------------|-----|-------------|----------------|---------------|-------|
    | Climate change, long term | kg CO2 eq (long) | air | unspecified | 1.0            | 10.1          | (...) |
    | Climate change, long term | kg CO2 eq (long) | air | indoor      | 1.0            | 10.1          | (...) |
    """

    return df_pivot


def generate_iwp_characterization_matrix_exiobase(
    type_iwp: str,
    version_iwp: str,
) -> pd.DataFrame:
    r"""
    Given a valid version and type of the IMPACT World+ method for life cycle impact assessment (LCIA)
    and the Ecoinvent database, returns a dataframe of the characterization matrix $\mathbf{Q}$.

    $$
    \mathbf{Q} = [Y \times R]
    $$

    where

    | Symbol | Description                                                                 |
    |--------|-----------------------------------------------------------------------------|
    | $Y$    | Number of individual impact assessment methods in the IMPACT World+ method. |
    | $R$    | Biosphere flows in the Ecoinvent biosphere database.                        |

    Notes
    -----
    Available versions:

    | IWP Version | IWP Type                              | Ecoinvent Version            | Exiobase Version |
    |-------------|---------------------------------------|------------------------------|------------------|
    | `2.0.1`     | `footprint_version`, `expert_version` | `3.8`, `3.9`                 | `None` (=v3)     |
    | `2.1`       | `footprint_version`, `expert_version` | `3.8`, `3.9`, `3.10`, `3.11` | `None` (=v3)     |

    See Also
    --------
    - Characterization Matrix $\mathbf{Q}$
        - Eqn.(8.26) in [Heijungs & Suh (2001)](https://doi.org/10.1007/978-94-015-9900-9), but see also ⚠️:
        - Eqn.(8.26) in [Errata of Heijungs & Suh (2001)](https://web.archive.org/web/20230505051343/https://personal.vu.nl/r.heijungs/computational/The%20computational%20structure%20of%20LCA%20-%20Errata.pdf)
    - IMPACT World Plus Method
        - [IMPACT World Plus Data on Zenodo](https://doi.org/10.5281/zenodo.1488368)
        - [IMPACT World Plus Website](https://www.impactworldplus.org)
        - Bulle, Cécile, et al. "IMPACT World+: a globally regionalized life cycle impact assessment method."
        _The International Journal of Life Cycle Assessment_ 24 (2019): 1653-1674.
        doi: [10.1007/s11367-019-01583-0](https://doi.org/10.1007/s11367-019-01583-0)

    Parameters
    ----------
    type_iwp : str
        Type of IMPACT World+ method  
        (e.g., `footprint_version`, `expert_version`)
    version_iwp : str
        Version of IMPACT World+  
        (e.g., `2.0.1`, `2.1`)
    type_iwp : str
        Type of IMPACT World+  
        (e.g., `footprint_version`, `expert_version`)

    Returns
    -------
    pd.DataFrame
        Characterization matrix $\mathbf{Q}$ for the specified version of IMPACT World+ and Exiobase.
    """

    df = _load_iwp_data(
        version_iwp=version_iwp,
        type_iwp=type_iwp,
        database='exiobase',
        version_database=None
    )
    """
    |                                                           | CO2 - combustion - air | CH4 - combustion - air | (...) |
    |-----------------------------------------------------------|------------------------|------------------------|-------|
    | Climate change, ecosystem quality, long term (PDF.m2.yr)  | 0.0025                 | 0.02                   | (...) |
    | Climate change, ecosystem quality, short term (PDF.m2.yr) | 0.0022                 | 0.03                   | (...) |
    """

    df.index = pd.MultiIndex.from_frame(
        df.index.to_series().apply(_extract_labels_from_exiobase_index),
        names=['Impact Category', 'CF Unit']
    )
    df = df.fillna(0.0)
    """
    |                                               |           | CO2 - combustion - air | CH4 - combustion - air | (...) |
    |-----------------------------------------------|-----------|------------------------|------------------------|-------|
    | Climate change, ecosystem quality, long term  | PDF.m2.yr | 0.0025                 | 0.02                   | (...) |
    | Climate change, ecosystem quality, short term | PDF.m2.yr | 0.0022                 | 0.03                   | (...) |
    """

    return df


def generate_iwp_characterization_matrix_ecoinvent_and_exiobase(
    type_iwp: str,
    version_iwp: str,
    version_ecoinvent: str,
) -> pd.DataFrame:
    r"""
    Given a valid version and type of the IMPACT World+ (IWP) method for life cycle impact assessment (LCIA)
    and the Ecoinvent database, returns a dataframe of the characterization matrix $\mathbf{Q}$.

    $$
    \mathbf{Q} = [Y \times (R_{ecoinvent} + R_{exiobase})]
    $$

    where

    | Symbol | Description                                                                 |
    |--------|-----------------------------------------------------------------------------|
    | $Y$    | Number of individual impact assessment methods in the IMPACT World+ method. |
    | $R_{ecoinvent}$ | Biosphere flows in the Ecoinvent biosphere database.               |
    | $R_{exiobase}$  | (Environmental) satellites of Exiobase .                           |

    Notes
    -----
    Available versions:

    | IWP Version | IWP Type                              | Ecoinvent Version            | Exiobase Version |
    |-------------|---------------------------------------|------------------------------|------------------|
    | `2.0.1`     | `footprint_version`, `expert_version` | `3.8`, `3.9`                 | `None` (=v3)     |
    | `2.1`       | `footprint_version`, `expert_version` | `3.8`, `3.9`, `3.10`, `3.11` | `None` (=v3)     |

    See Also
    --------
    - Characterization Matrix $\mathbf{Q}$
        - Eqn.(8.26) in [Heijungs & Suh (2001)](https://doi.org/10.1007/978-94-015-9900-9), but see also ⚠️:
        - Eqn.(8.26) in [Errata of Heijungs & Suh (2001)](https://web.archive.org/web/20230505051343/https://personal.vu.nl/r.heijungs/computational/The%20computational%20structure%20of%20LCA%20-%20Errata.pdf)
    - IMPACT World Plus Method
        - [IMPACT World Plus Data on Zenodo](https://doi.org/10.5281/zenodo.1488368)
        - [IMPACT World Plus Website](https://www.impactworldplus.org)
        - Bulle, Cécile, et al. "IMPACT World+: a globally regionalized life cycle impact assessment method."
        _The International Journal of Life Cycle Assessment_ 24 (2019): 1653-1674.
        doi: [10.1007/s11367-019-01583-0](https://doi.org/10.1007/s11367-019-01583-0)

    Parameters
    ----------
    type_iwp : str
        Type of IMPACT World+ method  
        (e.g., `footprint_version`, `expert_version`)
    version_iwp : str
        Version of IMPACT World+  
        (e.g., `2.0.1`, `2.1`)
    type_iwp : str
        Type of IMPACT World+  
        (e.g., `footprint_version`, `expert_version`)

    Returns
    -------
    pd.DataFrame
        Characterization matrix $\mathbf{Q}$ for the specified version of IMPACT World+ and Exiobase.
    """
    df_ecoinvent = generate_iwp_characterization_matrix_ecoinvent(
        type_iwp=type_iwp,
        version_iwp=version_iwp,
        version_ecoinvent=version_ecoinvent
    )
    """
    |                           |                  |     |             | Carbon dioxide | Methane       | (...) |
    |---------------------------|------------------|-----|-------------|----------------|---------------|-------|
    | Climate change, long term | kg CO2 eq (long) | air | unspecified | 1.0            | 10.1          | (...) |
    | Climate change, long term | kg CO2 eq (long) | air | indoor      | 1.0            | 10.1          | (...) |
    """

    df_ecoinvent = df_ecoinvent.groupby(level=['Impact category', 'CF unit']).sum()
    """
    |                           |                  | Carbon dioxide | Methane       | (...) |
    |---------------------------|------------------|----------------|---------------|-------|
    | Climate change, long term | kg CO2 eq (long) | 1.0            | 10.1          | (...) |
    """

    df_exiobase = generate_iwp_characterization_matrix_exiobase(
        type_iwp=type_iwp,
        version_iwp=version_iwp
    )
    """
    |                                               |           | CO2 - combustion - air | CH4 - combustion - air | (...) |
    |-----------------------------------------------|-----------|------------------------|------------------------|-------|
    | Climate change, ecosystem quality, long term  | PDF.m2.yr | 0.0025                 | 0.02                   | (...) |
    | Climate change, ecosystem quality, short term | PDF.m2.yr | 0.0022                 | 0.03                   | (...) |
    """

    with logtimer("combining Ecoinvent and Exiobase characterization matrices."):
        df_both = pd.concat(
            [df_ecoinvent, df_exiobase], axis=1, join='inner'
        )

    return df_both
# %%
