# %%

import pandas as pd
from pathlib import Path
import uuid
from greengraph.utility.logging import logtimer
import networkx as nx

path = Path('/Users/michaelweinold/data/ecoinvent 3.11_LCIA_implementation/LCIA Implementation 3.11.xlsx')
# 3.10 file takes forever to merge...whyever?!

def load_ecoinvent_characterization_data(
    path: Path,
    version: str,
) -> list:
    _versions_name_units = {
        "3.11": "CFs",
        "3.10": "CFs",
    }
    if version not in _versions_name_units:
        raise ValueError(
            f"Version {version} not supported. Supported versions are: {_versions_name_units.keys()}"
        )

    with logtimer('reading Ecoinvent characterization data from Excel file.'):
        df_cf_edges = pd.read_excel(
            path,
            sheet_name="CFs",
            header=0
        )
        df_units = pd.read_excel(
            path,
            sheet_name="Indicators",
            header=0
        )
    
    with logtimer('preparing Ecoinvent characterization data.'):
        df_cf_edges_with_units = pd.merge(
            df_cf_edges,
            df_units,
            on=['Method', 'Category', 'Indicator'],
            how="left"
        )
        df_cf_edges_with_units.columns = df_cf_edges_with_units.columns.str.lower()

        df_cf = df_cf_edges_with_units[['method', 'category', 'indicator', 'indicator unit']].drop_duplicates()
        df_cf['uuid'] = [str(uuid.uuid4()) for _ in range(len(df_cf))]

        df_cf_edges_with_units = df_cf_edges_with_units.merge(
            df_cf[['method', 'category', 'indicator', 'uuid']],
            on=['method', 'category', 'indicator'],
            how="left",
        )[['name', 'uuid', 'cf']]
    
    return {
        'list_dicts_cf_nodes': df_cf.to_dict(orient='records'),
        'list_dicts_cf_edges': df_cf_edges_with_units.to_dict(orient='records')
    }

out = load_ecoinvent_characterization_data(path=path, version='3.11')

list_dicts_cf_nodes = out['list_dicts_cf_nodes']
list_dicts_cf_edges = out['list_dicts_cf_edges']

# %%

from pathlib import Path
import networkx as nx
from greengraph.importers.databases.ecoinvent import _prepare_ecoinvent_node_and_edge_lists

from greengraph.importers.databases.ecoinvent import (
    _extract_ecospold_xml_files,
    _prepare_ecoinvent_node_and_edge_lists,
)

ecospold_xml_files = _extract_ecospold_xml_files(
    path=Path('/Users/michaelweinold/data/ecoinvent_3.11_cutoff_lcia_ecoSpold02'),
)

ecoinvent_node_and_edge_data = _prepare_ecoinvent_node_and_edge_lists(
    process_nodes=ecospold_xml_files['process_nodes'],
    product_nodes=ecospold_xml_files['product_nodes'],
    ecosphere_flows_mapping=ecospold_xml_files['ecosphere_flows_mapping'],
    technosphere_edges=ecospold_xml_files['technosphere_edges'],
    ecosphere_edges=ecospold_xml_files['ecosphere_edges'],
)

from greengraph.importers.databases.generic import graph_system_from_node_and_edge_lists


G = graph_system_from_node_and_edge_lists(
    name_system="ecoinvent 3.11",
    assign_new_uuids=True,
    str_production_nodes_uuid="brightway_code_process",
    str_extension_nodes_uuid="brightway_code_extension",
    list_dicts_production_nodes_metadata=ecoinvent_node_and_edge_data['nodes_production'],
    list_dicts_extension_nodes_metadata=ecoinvent_node_and_edge_data['nodes_extension'],
    list_tuples_production_edges=ecoinvent_node_and_edge_data['edges_production'],
    list_tuples_extension_edges=ecoinvent_node_and_edge_data['edges_biosphere'],
)

# %%

GG = nx.MultiDiGraph()

GG.add_nodes_from(
    [
        (
            node['uuid'], 
            {key: value for key, value in node.items() if key != 'uuid'}
        )
        for node in list_dicts_cf_nodes
    ]
)

GG.add_edges_from(
    [
        (
            dict_names_to_uuids.get(edge['name']),
            edge['uuid'],
            edge['cf']
        ) for edge in list_dicts_cf_edges
    ]
)

# %%

GG = nx.MultiDiGraph()

GG.add_nodes_from(
    [
        (
            node['uuid'], 
            {key: value for key, value in node.items() if key != 'uuid'}
        )
        for node in list_dicts_cf_nodes
    ]
)

GG.add_edges_from(
    [
        (
            [node for node, attr in G.nodes(data=True) if attr['name']==edge['name']][0],
            edge['uuid'],
            edge['cf']
        ) for edge in list_dicts_cf_edges
    ]
)

# %%

from greengraph.utility.data import create_dynamic_lookup_dictionary

dict_lookup = create_dynamic_lookup_dictionary(
    list_dicts=[
        {**attr, 'uuid': node}
        for node, attr in G.nodes(data=True)
        if attr.get('type') == 'extension'
    ],
    list_key_fields=['name'],
    value_field='uuid'
)

# %%

[
    dict_lookup.get(tuple([edge['name']]))
    for edge in list_dicts_cf_edges[0:5]
]