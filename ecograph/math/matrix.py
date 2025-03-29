import networkx as nx
import numpy as np
import logging

def calculate_production_vector(
    A: np.ndarray,
    f: np.ndarray,
) -> np.ndarray:
    """
    Calculate the production vector of a system given its adjacency matrix and flow vector.

    Parameters
    ----------
    A : np.ndarray
        Adjacency matrix representing the system.
    f : np.ndarray
        Flow vector.

    Returns
    -------
    np.ndarray
        Inventory vector.
    """
    logging.info(
        "Calculating production vector with adjacency matrix A of shape %s and flow vector f of shape %s.",
        A.shape,
        f.shape,
    )
    logging.info("Using numpy version: %s", np.__version__)
    logging.info("Using BLAS system: %s", np.__config__.get_info('blas_opt_info').get('libraries', 'Unknown'))
    return np.linalg.inv(np.eye(A.shape[0]) - A) @ f


def calculate_inventory_vector(
    B: np.ndarray,
    x: np.ndarray,
) -> np.ndarray:
    """
    Calculate the inventory vector of a system given its adjacency matrix and flow vector.

    Parameters
    ----------
    B : np.ndarray
        Biosphere matrix.
    x : np.ndarray
        Production vector.

    Returns
    -------
    np.ndarray
        Inventory vector.
    """
    return np.linalg.inv(np.eye(A.shape[0]) - A) @ f


def calculate_inventory_matrix(
    B: np.ndarray,
    x: np.ndarray,
) -> np.ndarray:
    """
    Calculate the inventory matrix of a system given its adjacency matrix and flow vector.
    """
    return


def calculate_impact_vector(
    Q: np.ndarray,
    g: np.ndarray,
) -> np.ndarray:
    """
    Calculate the impact vector of a system given its adjacency matrix and flow vector.
    """
    return np.linalg.inv(np.eye(Q.shape[0]) - Q) @ x


def calculate_impact_score(
    Q: np.ndarray,
    g: np.ndarray,
) -> np.ndarray:
    """
    Calculate the impact score of a system given its adjacency matrix and flow vector.
    """
    return np.linalg.inv(np.eye(Q.shape[0]) - Q) @ g