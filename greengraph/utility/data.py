# %%
def create_dynamic_lookup_dictionary(
    list_dicts: list[dict],
    list_key_fields: list[str],
    value_field: str,
) -> dict:
    """
    Creates a lookup dictionary from a list of dictionaries based on dynamic keys.

    Args:
        list_dicts (list): The list of dictionaries to process (e.g., your list2).
        list_key_fields (list): A list of string key names whose values will form the
                           composite key (as a tuple) for the lookup dictionary.
                           Example: ['name', 'system']
        value_field (str): The string key name whose value will be the value
                           in the lookup dictionary. Example: 'uuid'

    Returns:
        dict: A dictionary where keys are tuples of values corresponding to
              list_key_fields and values are the corresponding value from value_field.
              Entries are only added if all list_key_fields are present in the source
              dictionary item.

              
    For a list of dictionaries:

    ```python
    [
        {'name': 'A', 'system': 'X', 'uuid': '123'},
        {'name': 'B', 'system': 'X', 'uuid': '456'},
        {'name': 'A', 'system': 'Y', 'uuid': '789'},
    ]
    ```

    the function will create a lookup dictionary:

    ```python
    {
        ('A', 'X'): '123',
        ('B', 'X'): '456',
        ('A', 'Y'): '789',
    }
    ```

    This allows for highly performant lookups.
    For example, dictionaries from another list of dictionaries:

    ```python
    [
        {'name': 'A', 'system': 'X'},
        {'name': 'B', 'system': 'X'},
        {'name': 'A', 'system': 'Y'},
    ]
    ```

    can be matched to the first list using the lookup dictionary:

    ```python
    lookup_dict = create_dynamic_lookup_dictionary(
        list_dicts,
        list_key_fields=['name', 'system'],
        value_field='uuid'
    )
    for item in list_dicts:
    ```



    Example
    -------
    ```python
    [
        {'name': 'A', 'system': 'X', 'uuid': '123'},
        {'name': 'B', 'system': 'X', 'uuid': '456'},
        {'name': 'A', 'system': 'Y', 'uuid': '789'},
    ]
    ```

    """
    lookup_dict = {}

    for item in list_dicts:
        key_tuple_values = tuple([item.get(k) for k in list_key_fields])

        if None in key_tuple_values:
            raise ValueError(
                f"Missing key field values in item: {item}. "
                f"Expected keys: {list_key_fields}"
            )

        value = item.get(value_field)

        lookup_dict[key_tuple_values] = value

    return lookup_dict


create_dynamic_lookup_dictionary(
    list_dicts = [
        {'name': 'A', 'system': 'X', 'uuid': '123'},
        {'name': 'B', 'system': 'X', 'uuid': '456'},
        {'name': 'A', 'system': 'Y', 'uuid': '789'},
    ],
    list_key_fields = ['name', 'system'],
    value_field = 'uuid',
)