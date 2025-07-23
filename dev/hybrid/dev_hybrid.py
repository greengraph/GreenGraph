# %%
from importlib import resources
import json

import pickle
#with open('/Users/michaelweinold/github/GreenGraph/dev/Geco.pkl', 'rb') as f:
#    Geco = pickle.load(f)

with open('/Users/michaelweinold/github/GreenGraph/dev/Gexio.pkl', 'rb') as f:
    Gexio = pickle.load(f)

#concordance = {}
#with resources.open_text("greengraph.data.concordance", "geography_ecoinvent_exiobase.json") as file:
#    concordance = json.load(file)

# %%

df = pd.read_excel(
    "/Users/michaelweinold/github/pylcaio/src/Data/ecoinvent/ei3.10/mappings/filters.xlsx",
    sheet_name="Hybridized processes",
    header=0,
).dropna(axis=0, how='any')

from greengraph.core import GreenMultiDiGraph
H = GreenMultiDiGraph()





def option_lookup():
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