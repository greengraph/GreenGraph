# %%

import pandas as pd
import itertools
from typing import Any, Iterable

from greengraph.importers.databases.inputoutput import exiobase
from greengraph.utility.search import (
    _dict_to_tuple,
)

# %%

import pickle
with open('/Users/michaelweinold/github/GreenGraph/dev/Geco.pkl', 'rb') as f:
    Geco = pickle.load(f)

with open('/Users/michaelweinold/github/GreenGraph/dev/Gexio.pkl', 'rb') as f:
    Gexio = pickle.load(f)

# %%

df = pd.read_excel(
    "/Users/michaelweinold/github/pylcaio/src/Data/ecoinvent/ei3.10/mappings/filters.xlsx",
    sheet_name="Hybridized processes",
    header=0,
).dropna(axis=0, how='any')

# %%

import json
from importlib import resources




# %%

# CONCORDANCE (ALL?)


from greengraph.core import GreenMultiDiGraph
H = GreenMultiDiGraph()

set_locations_exio = {x for item in concordance.values() for x in (item if isinstance(item, list) else [item])}

def get_exiobase_region_from_ecoinvent_location(
    ecoinvent_location: str,
) -> str | list[str]:
    """
    Get the Exiobase region corresponding to an Ecoinvent location.
    
    Parameters
    ----------
    ecoinvent_location : str
        The Ecoinvent location code.
    
    Returns
    -------
    str
        The corresponding Exiobase region code.
    """
    concordance = {}
    with resources.open_text("greengraph.data.concordance", "geography_ecoinvent_exiobase.json") as file:
        concordance = json.load(file)

    set_exio_regions = {x for item in concordance.values() for x in (item if isinstance(item, list) else [item])}

    if not isinstance(ecoinvent_location, str):
        raise ValueError("Ecoinvent location code must be a string.")
    
    if ecoinvent_location in set_exio_regions:
        return ecoinvent_location
    elif isinstance(concordance[ecoinvent_location], str):
        return concordance[ecoinvent_location]
    elif isinstance(concordance[ecoinvent_location], list):
        return concordance[ecoinvent_location]
    else:
        return raise ValueError(
            f"Location '{ecoinvent_location}' not found in concordance or not a valid type."
        )



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


# %%

def option_getnode():
    lst = []
    for i, row_process in df.iterrows():
        """
        Case 1

        One-to-one concordance of ecoinvent process to exiobase sector

        Example
        -------
        ```
        loc_process='US'
        concordance['US']='US'
        ```
        """
        if row_process['location'] in set_locations_exio:
            node_sector = [
                node for node, attr in Gexio.nodes(data=True)
                if attr['name'] == row_process['exiobase_sector'] and
                attr['location'] == row_process['location']
            ]
        
        # lst.append(row_process)

# %%

# CONCORDANCE (GEOGRAPHIC)

import json
from importlib import resources

concordance = {}
with resources.open_text("greengraph.data.concordance", "geography_ecoinvent_exiobase.json") as file:
    concordance = json.load(file)

# loop through the different processes to-be-hybridized
for col in tqdm(self.H.columns, leave=True):
    act = bw2.Database(self.db_name).get(col)
    # extract location and corresponding exiobase sector
    geo = act.as_dict()['location']
    sector = self.filter['Hybridized processes'].loc[
        self.filter['Hybridized processes'].code == act.as_dict()['code'], 'exiobase_sector'].iloc[0]
    # if ecoinvent process location is in exiobase regions (US -> US)
    if geo in list(self.H.index.levels[0]):
        self.H.loc[(geo, sector), col] = 1
    # if it needs some mapping
    elif geo in self.concordance_geos.keys():
        # it's a country, not a region (e.g., AR -> WL)
        if type(self.concordance_geos[geo]) == str:
            self.H.loc[(self.concordance_geos[geo], sector), col] = 1
        # it's a region (e.g., RNA -> CA + US)
        else:
            # then we need to do some weighted averages based on production values of the x vector of exiobase
            self.H.loc[:, col] = (self.io.x.loc(axis=0)[self.concordance_geos[geo], sector] /
                                    self.io.x.loc(axis=0)[self.concordance_geos[geo], sector].sum()).reindex(
                self.H.index).loc[:, 'indout'].fillna(0)
    # special case for the dynamic region of ecoinvent: RoW
    else:
        covered_geos_for_product = []
        # get all processes producing the reference product (wurst is way faster than bw2.search())
        filtering = ws.get_many(self.ei_wurst, ws.equals('reference product', act.as_dict()['reference product']))
        # extract the location of these processes
        for dataset in filtering:
            if dataset['code'] in list(self.filter['Hybridized processes'].code):
                covered_geos_for_product.append(dataset['location'])
        # only keep unique ones
        covered_geos_for_product = set(covered_geos_for_product)
        # remove RoW and GLO from set
        covered_geos_for_product = covered_geos_for_product - {'RoW'} - {'GLO'}
        # convert potential regions in countries
        covered_countries_for_product = [self.concordance_geos[i] for i in covered_geos_for_product]
        # convert potential list of lists as lists
        covered_countries_for_product = [x for xs in covered_countries_for_product for x in xs]
        # apply the weighted average for relevant countries to H
        self.H.loc[:, col] = (self.io.x.loc(axis=0)[
            [i for i in self.H.index.levels[0] if i not in covered_countries_for_product], sector]
            / self.io.x.loc(axis=0)[
                [i for i in self.H.index.levels[0] if
                                                i not in covered_countries_for_product], sector].sum()).reindex(
            self.H.index).loc[:, 'indout'].fillna(0)