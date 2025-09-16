# %%
import pandas as pd
import itertools
from typing import Any, Iterable
import json
from importlib import resources

from greengraph.importers.databases.inputoutput import exiobase
from greengraph.utility.search import (
    _dict_to_tuple,
)

def get_exiobase_region_from_ecoinvent_location(
    ecoinvent_location: str,
) -> str | list[str]:
    """
    Given a string of an Ecoinvent location code,
    returns the corresponding Exiobase region code or a list of region codes.

    See Also
    --------
    - [Ecoinvent Geographies (Support Article)](https://support.ecoinvent.org/geographies)
    - [Sheet `Countries` in Supporting Information S9 of the 2018 Stadler et al. article on Exiobase 3](https://doi.org/10.1111/jiec.12715)

    Example
    -------
    ```python
    >>> get_exiobase_region_from_ecoinvent_location("WEU")
    ['AT', 'BE', 'CH', 'DE', 'FR', 'NL']
    ```

    Warnings
    --------
    The Ecoinvent location code `RoW` (Rest of World) is not supported by this function.
    This is because `RoW` does not correspond to a specific Exiobase region.
    Instead, it is a "dynamic" region that depends on the context of the analysis.
    
    Parameters
    ----------
    ecoinvent_location : str
        The Ecoinvent location code.  
    
    Returns
    -------
    str | list[str]
        The corresponding Exiobase region code(s).  
        If the Ecoinvent location corresponds to a single Exiobase region,
        a single region code is returned as a string.  
        If the Ecoinvent location corresponds to multiple Exiobase regions,
        a list of region codes is returned.  

    Raises
    ------
    ValueError
        If the provided `ecoinvent_location` is not a string,
        or if it is `RoW`, or if the location is not found in the concordance.
    """
    if not isinstance(ecoinvent_location, str):
        raise ValueError("Ecoinvent location code must be a string.")
    if ecoinvent_location == "RoW":
        raise ValueError(
            "There is no concordance for the Ecoinvent dynamic location code 'RoW' (Rest of World). "
        )

    concordance = {}
    with resources.open_text("greengraph.hybrid._data.concordance", "geography_ecoinvent_exiobase.json") as file:
        concordance = json.load(file)

    set_exio_regions = {x for item in concordance.values() for x in (item if isinstance(item, list) else [item])}

    if ecoinvent_location in set_exio_regions:
        return ecoinvent_location
    elif isinstance(concordance[ecoinvent_location], str):
        return concordance[ecoinvent_location]
    elif isinstance(concordance[ecoinvent_location], list):
        return concordance[ecoinvent_location]
    else:
        raise ValueError(
            f"Location '{ecoinvent_location}' not found in concordance or not a valid type."
        )


def option_lookup():
    """
    
    ![](../../_media/concordance/geographic_concordance.svg)
    
    Diagram of the possible cases of geographic concordance
    between Ecoinvent processes and Exiobase sectors.
    
    """
    lst = []
    for i, row_process in df.iterrows():
        node_process = Geco.hashsearch(
            dict_search_attributes={
                'name': row_process['name'],
                'product': row_process['reference product'],
                'geography code': row_process['location'],
            },
            dict_filter_attributes={
                'type': 'production'
            }
        )
        """
        Case 1

        One-to-one concordance of Ecoinvent process to Exiobase sector
        and Ecoinvent location code equivalent to Exiobase location code.

        Example
        -------
        Ecoinvent process: 'US' (United States)
        Exiobase sector: 'US' (United States)

        JSON file
        ---------
        (Ecoinvent location: Exiobase location)
        ```
        "US": "US"
        ```
        """
        if row_process['location'] in set_locations_exio:
            node_sector = Gexio.hashsearch(
                dict_search_attributes={
                    'name': row_process['exiobase_sector'],
                    'location': row_process['location'],
                },
                dict_filter_attributes={
                    'type': 'production'
                }
            )
            u = node_process
            v = node_sector
            d = {'type': 'concordance', 'weight': 1.0}
        """
        Case 2
        
        One-to-one concordance of Ecoinvent process to Exiobase sector
        but Ecoinvent location code NOT equivalent to Exiobase location code.

        Example
        -------
        Ecoinvent process: "CA-QC" (Canada, Quebec)
        Exiobase sector: "CA" (Canada)

        JSON file
        ---------
        (Ecoinvent location: Exiobase location)
        ```
        "CA-QC": "CA"
        ```
        """
        if isinstance(concordance[row_process['location']], str) and not row_process['location'] == 'RoW': # single location, not list of locations
            node_sector = Gexio.hashsearch(
                dict_search_attributes={
                    'name': row_process['exiobase_sector'],
                    'location': concordance[row_process['location']],
                },
                dict_filter_attributes={
                    'type': 'production'
                }
            )
            u = node_process
            v = node_sector
            d = {'type': 'concordance', 'weight': 1.0}
        """
        Case 3

        One-to-many concordance of Ecoinvent process to Exiobase sectors.

        Notes
        -----
        This is the case for Ecoinvent regions like "WEU" (Western Europe), etc.

        JSON file
        ---------
        (Ecoinvent location: Exiobase locations)
        ```
        "WEU": ["AT", "BE", "CH", "DE", "FR", "NL"]
        ```
        """
        if isinstance(concordance[row_process['location']], list): # list of locations
            dict_sectors_annual_production = {}
            total_annual_production = 0.0
            for location in concordance[row_process['location']]:
                node_sector = Gexio.hashsearch(
                    dict_search_attributes={
                        'name': row_process['exiobase_sector'],
                        'location': location,
                    },
                    dict_filter_attributes={
                        'type': 'production'
                    }
                )
                if node_sector is not None:
                    dict_sectors_annual_production[node_sector] = Gexio.nodes[node_sector]['annual production']
                    total_annual_production += Gexio.nodes[node_sector]['annual production']
            for node_sector, annual_production in dict_sectors_annual_production.items():
                u = node_process
                v = node_sector
                d = {
                    'type': 'concordance',
                    'weight': annual_production / total_annual_production if annual_production > 0 else 0.0
                }
                print(node_sector)

        # lst.append(row_process)
        """
        Case 4

        Ecoinvent "rest of world" process, which is a "dynamic" region.

        JSON file
        ---------
        The JSON file does not contain a specific entry for "RoW", since this is a dynamic region.
        """
        if row_process['location'] == 'RoW':
            list_all_process_nodes = Geco.hashsearch(
                dict_search_attributes={
                    'reference product': row_process['reference product'],
                },
                dict_filter_attributes={
                    'type': 'production'
                },
                enforce_unique_results=False
            )
            set_locations_ecoinvent_all_process_nodes = set(node_process['location'] for node_process in list_all_process_nodes) - {'RoW', 'GLO'}
            generator_regions_exiobase_all_process_nodes = (get_exiobase_region_from_ecoinvent_location(location) for location in set_locations_ecoinvent_all_process_nodes)
            set_regions_exiobase_all_process_nodes = set(itertools.chain.from_iterable(generator_regions_exiobase_all_process_nodes))

            dict_sectors_annual_production = {}
            total_annual_production = 0.0
            for region in set_regions_exiobase_all_process_nodes:
                node_sector = Gexio.hashsearch(
                    dict_search_attributes={
                        'name': row_process['exiobase_sector'],
                        'location': region,
                    },
                    dict_filter_attributes={
                        'type': 'production'
                    }
                )
                if node_sector is not None:
                    dict_sectors_annual_production[node_sector] = Gexio.nodes[node_sector]['annual production']
                    total_annual_production += Gexio.nodes[node_sector]['annual production']

            for node_sector, annual_production in dict_sectors_annual_production.items():
                u = node_process
                v = node_sector
                d = {
                    'type': 'concordance',
                    'weight': annual_production / total_annual_production if annual_production > 0 else 0.0
                }
                print(node_sector)