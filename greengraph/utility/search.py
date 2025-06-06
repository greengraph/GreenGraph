# %%
import networkx as nx
import copy
from functools import lru_cache
from typing import Optional


def _make_hashable(value) -> object:
    """
    Given a value, returns a hashable version of it.
    
    Recursively converts mutable collections (dict, list, set) in a value
    into their hashable counterparts (tuple-of-items, tuple, frozenset).

    Example
    -------
    ```python
    >>> _make_hashable([2, 3])
    frozenset({2, 3})
    ```

    Parameters
    ----------
    value : any
        The value to be converted into a hashable type.
    
    Returns
    -------
    object
        A hashable version of the input value.
    
    Raises
    ------
    TypeError
        If the value is of a type that cannot be converted to a hashable type.
    """
    if isinstance(value, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in value.items()))
    elif isinstance(value, list):
        return frozenset(_make_hashable(item) for item in value)
    elif isinstance(value, set):
        return frozenset(_make_hashable(item) for item in value)

    try:
        hash(value)
        return value
    except TypeError:
        raise TypeError(f"Value of type {type(value).__name__}: {value!r} is not hashable and not handled.")


def _dict_to_tuple(d) -> tuple:
    """
    Given a dictionary, returns a tuple of its items sorted by key.

    Converts a dictionary (potentially with nested unhashable types)
    into a hashable tuple of sorted items.

    Example
    -------
    ```python
    >>> _dict_to_tuple({'a': 1, 'b': [2, 3]})
    (
        ('a', 1),
        ('b', frozenset({2, 3}))
    )
    ```

    Parameters
    ----------
    d : dict
        The dictionary to be converted into a hashable tuple.
    
    Returns
    -------
    tuple
        A hashable tuple of sorted items from the input dictionary.

    Raises
    ------
    TypeError
        If the input is not a dictionary.  
        If any of the dictionary values are unhashable.
    """
    if not isinstance(d, dict):
        raise TypeError(f"Input must be a dictionary, got {type(d).__name__}")
    try:
        list_dictionary_items = []
        for k, v in d.items():
            list_dictionary_items.append((k, _make_hashable(v)))
        return tuple(sorted(list_dictionary_items))
    except TypeError as e:
        raise TypeError(f"Failed to create hashable key for dict: {d!r}. Original error: {e}")


def _build_lookup_dictionary(
    G: nx.MultiDiGraph,
    lookup_attributes: tuple[str],
    node_filter: Optional[dict[str, Any]] = None,
    check_unique: Optional[bool] = True
) -> dict:
    """
    Given a NetworkX graph and a list of key fields, creates a lookup dictionary.
    
    For a NetworkX Graph of the kind:

    ```python
    {
        '123': {'name': 'A', 'system': 'X'},
        '456': {'name': 'B', 'system': 'X'},
        '789': {'name': 'A', 'system': 'Y'},
    }
    ```

    and a tuple of lookup attributes like `('name', 'system')`,
    the function will create a lookup dictionary:

    ```python
    {
        ('A', 'X'): '123',
        ('B', 'X'): '456',
        ('A', 'Y'): '789',
    }
    ```

    This allows for highly performant lookups.

    Example
    -------
    ```python
    >>> G = nx.MultiDiGraph()
    >>> G.add_node('123', name='A', system='X')
    >>> G.add_node('456', name='B', system='X')
    >>> G.add_node('789', name='A', system='Y')
    >>> lookup = create_dynamic_lookup_dictionary(G=G, node_type='system', list_key_fields=['name'])
    ```

    Parameters
    ----------
    G : nx.MultiDiGraph
        The NetworkX graph from which to create the lookup dictionary.
    lookup_attributes : tuple[str]
        A tuple of lookup attributes. 
    node_type : str
        The type of nodes to include in the lookup dictionary.  
        This can be used to reduce the size of the lookup dictionary by filtering nodes based on their type.
    check_unique : bool
        If True, checks that the combination of attributes is unique across all nodes in the graph.
        If False, allows for non-unique combinations, which can lead to overwriting entries in the dictionary.

    Returns
    -------
    dict
        A dictionary where the keys are tuples of attribute values and the values are node identifiers.
        The keys are created by converting the specified attributes of the nodes into tuples.

    Raises
    ------
    ValueError
        If `check_unique` is True and the combination of attributes is not unique across all nodes in the graph.
    TypeError
        If the `lookup_attributes` is not a tuple or if the attributes are not present in the node data.
    """
    
    if not isinstance(lookup_attributes, tuple):
        raise TypeError(f"Expected lookup_attributes to be a tuple, but got {type(lookup_attributes).__name__}.")
    
    sorted_lookup_attributes = tuple(sorted(lookup_attributes))
    dict_lookup = {}

    for node, attr in G.nodes(data=True):
        if node_filter is not None:
            if not all(attr.get(key) == value for key, value in node_filter.items()):
                continue
        try:
            lookup_key = tuple(
                _make_hashable(attr.get(key)) for key in sorted_lookup_attributes
            )
        except KeyError as e:
            raise KeyError(f"Node {node} is missing one of the lookup attributes: {sorted_lookup_attributes}.") from e
        
        if lookup_key in dict_lookup:
            if check_unique:
                raise ValueError(
                    f"Duplicate key found in lookup dictionary: {lookup_key}. "
                    "This indicates that the combination of attributes is not unique."
                )
            else:
                continue
        else:
            dict_lookup[lookup_key] = node
    
    return dict_lookup

def _remove_duplicate_dictionaries(list_dicts) -> list[dict]:
    """
    Given a list of dictionaries, removes all duplicates.


    Example
    -------
    ```python
    >>> list_dicts = [{'name': 'A'}, {'name': 'B'}, {'name': 'A'}]
    >>> add_shared_uuids_to_list_of_dicts(list_dicts)
    [
        {'name': 'A'},
    ]
    ```

    Parameters
    ----------
    list_dicts : list[dict]
        A list of dictionaries.

    Returns
    -------
    list[dict]
        A list of dictionaries with added UUIDs.
    """
    list_seen_metadata_tuples = set()
    list_output = []

    for i, dict_node_metadata in enumerate(list_dicts):
        if not isinstance(dict_node_metadata, dict):
            raise TypeError(f"Expected a list of dictionaries, but got {type(dict_node_metadata).__name__} at index {i}.")

        node_metadata_tuple = _dict_to_tuple(dict_node_metadata)
        if node_metadata_tuple in list_seen_metadata_tuples:
            pass
        else:
            list_seen_metadata_tuples.add(node_metadata_tuple)
            list_output.append(copy.deepcopy(dict_node_metadata))

    return list_output