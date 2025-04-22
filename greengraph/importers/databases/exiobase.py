# %%
import networkx as nx
import pandas as pd
import numpy as np
import scipy as sp
from pathlib import Path
import pathlib
from pandas.api.types import is_numeric_dtype

from greengraph.utility.logging import logtimer


def _format_exiobase_matrices(
    path_exiobase_root_directory: Path
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Format EXIOBASE matrices for use in greengraph.

    Parameters
    ----------
    path_exiobase_root_directory : Path
        Path to the EXIOBASE root directory.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        Formatted A and S matrices.

    Raises
    ------
    TypeError
        If path_exiobase_root_directory is not a pathlib.Path object.
    """
    if not isinstance(path_exiobase_root_directory, pathlib.Path):
        raise TypeError("path_exiobase_root_directory must be a pathlib.Path object")

    df_A = pd.read_csv(
        path_exiobase_root_directory / 'A.txt',
        delimiter='\t',
        skiprows=3,
        header=None
    )
    df_A_metadata = df_A.iloc[:, [0, 1]].copy()
    df_A.drop(columns=[0, 1], inplace=True)
    df_A_metadata.columns = ['location', 'name']
    df_A_metadata['unit'] = 'USD'

    df_S = pd.read_csv(
        path_exiobase_root_directory / 'satellite' / 'S.txt',
        delimiter='\t',
        skiprows=3,
        header=None
    )
    df_S.drop(columns=[0], inplace=True)
    df_S_metadata = pd.read_csv(
        path_exiobase_root_directory / 'satellite' / 'unit.txt',
        delimiter='\t',
        skiprows=1,
        header=None
    )
    df_S_metadata.columns = ['name', 'unit']

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
        'A_metadata': df_A_metadata,
        'S': df_S,
        'S_metadata': df_S_metadata
    }