# %%

import uuid
import networkx as nx
import copy

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


def _create_dynamic_lookup_dictionary(
    G: nx.MultiDiGraph,
    node_type: str,
    list_attributes: list[str],
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

    the function will create a lookup dictionary:

    ```python
    {
        (('name', 'A'), ('system', 'X')): '123',
        (('name', 'B'), ('system', 'X')): '456',
        (('name', 'A'), ('system', 'Y')): '789',
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
    node_type : str
        The type of nodes to include in the lookup dictionary.
    list_attributes : list[str]
        The list of attributes to use as keys in the lookup dictionary.

    Returns
    -------
    dict
        A dictionary where the keys are tuples of attribute values and the values are node identifiers.
        The keys are created by converting the specified attributes of the nodes into tuples.
    """
    dict_lookup = {
        _dict_to_tuple(
            {
                key: attr[key] for key in list_attributes
                if key in attr
            }
        ): node
        for node, attr in G.nodes(data=True)
        if attr.get('type') == node_type
    }
    return dict_lookup



def _add_shared_uuids_to_list_of_dicts(list_dicts) -> list[dict]:
    """
    Given a list of dictionaries, adds a UUID to each dictionary.

    Notes
    -----
    Identical dictionaries in the input list will receive the same UUID.


    Example
    -------
    ```python
    >>> list_dicts = [{'name': 'A'}, {'name': 'B'}, {'name': 'A'}]
    >>> add_shared_uuids_to_list_of_dicts(list_dicts)
    [
        {'name': 'A', 'uuid': '1234'},
        {'name': 'B', 'uuid': '5678'},
    ]

    Parameters
    ----------
    list_dicts : list[dict]
        A list of dictionaries.

    Returns
    -------
    list[dict]
        A list of dictionaries with added UUIDs.
    """
    dict_uuid_cache = {}
    list_output = []

    for i, dict_node_metadata in enumerate(list_dicts):
        if not isinstance(dict_node_metadata, dict):
            raise TypeError(f"Expected a list of dictionaries, but got {type(dict_node_metadata).__name__} at index {i}.")

        node_metadata_tuple = _dict_to_tuple(dict_node_metadata)
        if node_metadata_tuple in dict_uuid_cache:
            uuid_node = dict_uuid_cache[node_metadata_tuple]
        else:
            uuid_node = str(uuid.uuid4())
            dict_uuid_cache[node_metadata_tuple] = uuid_node

        dict_node_metadata_uuid = copy.deepcopy(dict_node_metadata)
        dict_node_metadata_uuid['uuid'] = uuid_node

        list_output.append(dict_node_metadata_uuid)

    return list_output