# %%

import pandas as pd


def load_impact_world_plus(
    version_iwp: str,
    type_iwp: str,
    database: str,
    version_database: str,
) -> pd.DataFrame:
    """
    Given a valid version of IMPACT World+ and the Ecoinvent database,
    returns a dataframe of the Excel sheets containing characterization factors.

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
      The International Journal of Life Cycle Assessment 24 (2019): 1653-1674.
      doi: [10.1007/s11367-019-01583-0](https://doi.org/10.1007/s11367-019-01583-0)

    Parameters
    ----------
    version_iwp : str
        Version of IMPACT World+
    version_ecoinvent : str
        Version of Ecoinvent

    Returns
    -------
    pd.DataFrame
        DataFrame containing characterization factors for the specified versions of IMPACT World+ and Ecoinvent.
    """

    "https://zenodo.org/records/14041258/files/impact_world_plus_2.1_expert_version_exiobase.xlsx?download=1"
    
    iwp_version_id = {
        '2.0.1': '8200703',
        '2.1': '14041258'
    }

    if version_database == None:
        version_database = ""

    return pd.read_excel(
        io=f"https://zenodo.org/record/{iwp_version_id[version_iwp]}/files/impact_world_plus_{version_iwp}_{type_iwp}_{database}_v{version_database}.xlsx?download=1",
        sheet_name='Sheet1',
        header=0,
        index_col=0,
        engine='openpyxl',
    )

# %%

load_impact_world_plus(
    version_iwp='2.1',
    type_iwp='expert_version',
    database='ecoinvent',
    version_database='3.10'
)