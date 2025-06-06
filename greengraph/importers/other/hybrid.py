# %%

import pandas as pd

from greengraph.importers.databases.inputoutput import exiobase
from greengraph.utility.search import (
    _dict_to_tuple,
    _create_dynamic_lookup_dictionary
)

# %%

df = pd.read_excel(
    "/Users/michaelweinold/github/pylcaio/src/Data/ecoinvent/ei3.10/mappings/filters.xlsx",
    sheet_name="Hybridized processes",
    header=0,
).dropna(axis=1, how='all')

df['geography code'] = df['location']
df['matching'] = df[['name', 'geography code']].to_dict(orient='records')
df['matching'] = df['matching'].apply(
    lambda row: _dict_to_tuple(row)
)

dict_lookup_eco = _create_dynamic_lookup_dictionary(
    G=Geco,
    node_type='production',
    list_attributes=['name', 'geography code']
)

df['matched'] = df['matching'].map(dict_lookup_eco)

# %%

Gexio = exiobase.create_graph(
        version='3.8.2',
        year=2021,
        type='pxp'
    )

# %%

import pickle
with open('/Users/michaelweinold/github/GreenGraph/dev/Geco.pkl', 'rb') as f:
    Geco = pickle.load(f)

# %%

dict_lookup = _create_dynamic_lookup_dictionary(
    G=Gexio,
    node_type='production',
    list_attributes=['name', 'location']
)

import json
from importlib import resources

conc = {}
with resources.open_text("greengraph.data.concordance", "geography_ecoinvent_exiobase.json") as file:
    conc = json.load(file)

df['matched2'] = df['matching']

# %%

# CONCORDANCE (ALL?)


from greengraph.core import GreenMultiDiGraph
H = GreenMultiDiGraph()

set_locations_exio = {x for item in conc.values() for x in (item if isinstance(item, list) else [item])}

def option_lookup():
    lst = []
    for i, row_process in df.iterrows():
        """
        Case 1

        One-to-one concordance of ecoinvent process to exiobase sector

        Example
        -------
        ```
        loc_process='US'
        conc['US']='US'
        ```
        """
        if row_process['location'] in set_locations_exio:
            node_sector = dict_lookup.get(
                (
                    ('location', row_process['location']),
                    ('name', row_process['exiobase_sector'])
                )
            )
            print(node_sector)
        
        # lst.append(row_process)


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
        conc['US']='US'
        ```
        """
        if row_process['location'] in set_locations_exio:
            node_sector = [
                node for node, attr in Gexio.nodes(data=True)
                if attr['name'] == row_process['exiobase_sector'] and
                attr['location'] == row_process['location']
            ]
            print(node_sector)
        
        # lst.append(row_process)

# %%

# CONCORDANCE (GEOGRAPHIC)

import json
from importlib import resources

conc = {}
with resources.open_text("greengraph.data.concordance", "geography_ecoinvent_exiobase.json") as file:
    conc = json.load(file)

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