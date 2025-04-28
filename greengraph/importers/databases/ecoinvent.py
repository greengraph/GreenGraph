# %%
import pandas as pd
import hashlib
from lxml import objectify
from dataclasses import dataclass
import pyecospold
from pyecospold.model_v2 import IntermediateExchange, Activity, FlowData
from pathlib import Path
import networkx as nx
from greengraph.utility.logging import logtimer

def _extract_ecospold_xml_masterdata_files(path: Path) -> dict:
    r"""
    Given a path to the root directory containing EcoSpold XML files, extracts
    the relevant `MasterData` XML files and returns a dictionary containing
    mappings for activities, products, geographies, and ecosphere flows.

    Notes
    -----

    - `activity_mapping`

    ```
    {
        (...)
        'f6d28af1-262b-472d-aaa2-9c887b59ff44': {
            'name': 'bitumen seal production, Alu80',
            'geography': 'Global',
            'start': '1994-01-01',
            'end': '2000-12-31',
            'type': 'ordinary transforming activity (default)'
        },
        (...)
    }
    ```

    - `activity_names_mapping`

    ```
    {
        (...)
        'e32fe5e6-8a68-4ae9-9c83-1abe8022b6b5': 'market for refractory, basic, packed',
        (...)
    }
    ```

    - `product_mapping`

    ```
    {
        (...)
        'a95b9d49-4114-40c6-9929-0c6c79db22d1': {
            'name': 'nickel concentrate, 16% Ni',
            'unit': 'kg',
            'comment': '',
            'product_information': '',
            'classifications': {
                'By-product classification': 'allocatable product',
                'CPC': '14220: Nickel ores and concentrates'
            }
        },
        (...)
    }
    ```

    - `geographies_mapping`

    ```
    {
        (...)
        '11311298-7d7e-11de-9ae2-0019e336be3a': 'Paraguay',
        (...)
    }
    ```

    - `ecosphere_flows_mapping`

    ```
    {
        (...)
        '6ab08314-53e1-4c4b-963f-3c6e6970273d': {
            'name': 'Chloride',
            'unit': 'kg',
            'chemical_formula': None,
            'CAS': '016887-00-6',
            'compartments': ['soil', 'agricultural'],
            'synonyms': []
        },
        (...)
    }
    ```

    See Also
    --------
    [Mutel (2023) "You just got an ecoinvent license. Now what?"](https://chris.mutel.org/how-to-use-ecoinvent.html)

    Parameters
    ----------
    path : Path
        Path to the directory containing the EcoSpold XML files.

    Returns
    -------
    dict
        A dictionary containing mappings for activities, products, geographies, and ecosphere flows.
    """

    NS = "{http://www.EcoInvent.org/EcoSpold02}"
    ACTIVITIES_FP = path / "MasterData" / "ActivityIndex.xml"
    PRODUCTS_FP = path / "MasterData" / "IntermediateExchanges.xml"
    GEOGRAPHIES_FP = path / "MasterData" / "Geographies.xml"
    ACTIVITY_NAME_FP = path / "MasterData" / "ActivityNames.xml"
    SPECIAL_ACTIVITY_TYPE_MAP: dict[int, str] = {
        0: "ordinary transforming activity (default)",
        1: "market activity",
        2: "IO activity",
        3: "Residual activity",
        4: "production mix",
        5: "import activity",
        6: "supply mix",
        7: "export activity",
        8: "re-export activity",
        9: "correction activity",
        10: "market group",
    }
    FLOWS_FP = path / "MasterData" / "ElementaryExchanges.xml"

    geographies_mapping = {
        elem.get("id"): elem.name.text
        for elem in objectify.parse(open(GEOGRAPHIES_FP))
        .getroot()
        .iterchildren(NS + "geography")
    }
    activity_names_mapping = {
        elem.get("id"): elem.name.text
        for elem in objectify.parse(open(ACTIVITY_NAME_FP))
        .getroot()
        .iterchildren(NS + "activityName")
    }
    activity_mapping = {
        elem.get("id"): {
            "name": activity_names_mapping[elem.get("activityNameId")],
            "geography": geographies_mapping[elem.get("geographyId")],
            "start": elem.get("startDate"),
            "end": elem.get("endDate"),
            "type": SPECIAL_ACTIVITY_TYPE_MAP[int(elem.get("specialActivityType"))],
        }
        for elem in objectify.parse(open(ACTIVITIES_FP))
        .getroot()
        .iterchildren(NS + "activityIndexEntry")
    }


    def _maybe_missing(
        element: objectify.ObjectifiedElement, attribute: str, pi: bool | None = False
    ):
        try:
            if pi:
                return element.productInformation.find(NS + "text")
            else:
                return getattr(element, attribute).text
        except AttributeError:
            return ""


    product_mapping = {
        elem.get("id"): {
            "name": elem.name.text,
            "unit": elem.unitName.text,
            "comment": _maybe_missing(elem, "comment"),
            "product_information": _maybe_missing(elem, "productInformation", True),
            "classifications": dict(
                [
                    (c.classificationSystem.text, c.classificationValue.text)
                    for c in elem.iterchildren(NS + "classification")
                ]
            ),
        }
        for elem in objectify.parse(open(PRODUCTS_FP)).getroot().iterchildren()
    }


    ecosphere_flows_mapping = {
        elem.get("id"): {
            "name": elem.name.text,
            "unit": elem.unitName.text,
            "chemical_formula": elem.get("formula") or None,
            "CAS": elem.get("casNumber") or None,
            "compartments": [
                elem.compartment.compartment.text,
                elem.compartment.subcompartment.text,
            ],
            "synonyms": [obj.text for obj in elem.iterchildren(NS + "synonym")],
        }
        for elem in objectify.parse(open(FLOWS_FP))
        .getroot()
        .iterchildren(NS + "elementaryExchange")
    }

    return {
        'activity_mapping': activity_mapping,
        'activity_names_mapping': activity_names_mapping,
        'product_mapping': product_mapping,
        'geographies_mapping': geographies_mapping,
        'product_mapping': product_mapping,
        'ecosphere_flows_mapping': ecosphere_flows_mapping,
    }


def _extract_ecospold_xml_files(
    path: Path,
) -> dict:
    r"""
    """

    dict_mapping = _extract_ecospold_xml_masterdata_files(path=path)
    activity_mapping = dict_mapping['activity_mapping']
    product_mapping = dict_mapping['product_mapping']

    INPUTS = ("Materials/Fuels", "Electricity/Heat", "Services", "From Technosphere (unspecified)")

    combined_nodes = []
    process_nodes, product_nodes = {}, {}
    technosphere_edges, ecosphere_edges = [], []


    def _get_process_id(edge: IntermediateExchange, activity: Activity) -> str:
        return edge.activityLinkId or activity.id


    def _reference_product(flows: FlowData) -> str:
        candidates = [
            edge for edge in flows.intermediateExchanges
            if edge.groupStr == "ReferenceProduct"
            and edge.amount != 0
        ]
        if not len(candidates) == 1:
            raise ValueError("Can't find reference product")
        return candidates[0].intermediateExchangeId

    _ = lambda str: str.encode("utf-8")


    def _unique_identifier(process_dict: dict, product_dict: dict, type: str) -> str:
        return hashlib.md5(
            _(process_dict["name"])
            + _(product_dict["name"])
            + _(product_dict["unit"])
            + _(process_dict["geography"])
            + _(type)
        ).hexdigest()

    @dataclass
    class TechnosphereEdge:
        source: str  # Our unique identifier
        target: str  # Our unique identifier
        amount: float
        positive: bool = True

    @dataclass
    class EcosphereEdge:
        flow: str     # ecoinvent UUID
        process: str  # Our unique identifier
        amount: float

    with logtimer('reading EcoSpold XML files'):
        for filepath in (path / "datasets").iterdir():
            if not filepath.name.endswith(".spold"):
                continue
            ecospold = pyecospold.parse_file_v2(filepath)
            activity = ecospold.activityDataset.activityDescription.activity[0]

            this_process = activity_mapping[activity.id]
            this_product = product_mapping[_reference_product(ecospold.activityDataset.flowData)]

            this_process_id = _unique_identifier(this_process, this_product, "process")
            this_product_id = _unique_identifier(this_process, this_product, "product")

            process_nodes[this_process_id] = (this_process, this_product)
            product_nodes[this_product_id] = (this_process, this_product)

            this_process_with_id = this_process.copy()
            this_process_with_id["id"] = this_process_id
            this_product_with_id = this_product.copy()
            this_product_with_id["id"] = this_product_id
            combined_nodes.append({
                    'process': this_process_with_id,
                    'product': this_product_with_id
                }
            )

            for edge in ecospold.activityDataset.flowData.intermediateExchanges:
                if not edge.amount:
                    continue

                other_process = activity_mapping[_get_process_id(edge=edge, activity=activity)]
                other_product = product_mapping[edge.intermediateExchangeId]
                other_product_id = _unique_identifier(other_process, other_product, "product")

                is_input_edge = edge.groupStr in INPUTS
                if is_input_edge:
                    technosphere_edges.append(TechnosphereEdge(
                        source=other_product_id,
                        target=this_process_id,
                        amount=edge.amount,
                        positive=False
                    ))
                else:
                    technosphere_edges.append(TechnosphereEdge(
                        source=this_process_id,
                        target=other_product_id,
                        amount=edge.amount,
                        positive=True
                    ))

            for edge in ecospold.activityDataset.flowData.elementaryExchanges:
                ecosphere_edges.append(EcosphereEdge(
                    flow=edge.elementaryExchangeId,
                    process=this_process_id,
                    amount=edge.amount
                ))

        return {
            "combined_nodes": combined_nodes,
            "process_nodes": process_nodes,
            "product_nodes": product_nodes,
            "technosphere_edges": technosphere_edges,
            "ecosphere_edges": ecosphere_edges,
        }

# %%

masterfiles = _extract_ecospold_xml_masterdata_files(Path('/Users/michaelweinold/data/ecoinvent 3.7.1_apos_ecoSpold02'))
out = _extract_ecospold_xml_files(Path('/Users/michaelweinold/data/ecoinvent 3.7.1_apos_ecoSpold02'))

# %%

combined_nodes = out['combined_nodes']
process_nodes = out['process_nodes']
product_nodes = out['product_nodes']
technosphere_edges = out['technosphere_edges']
ecosphere_edges = out['ecosphere_edges']
ecosphere_flows_mapping = masterfiles['ecosphere_flows_mapping']

# %%

import uuid


for item in combined_nodes:
    item['uuid'] = str(uuid.uuid4())
    item['type'] = 'technosphere'

df_lookup_production = pd.DataFrame(
    [
        {
            'uuid': i['uuid'],
            'process_id': i['process']['id'],
            'product_id': i['product']['id']
        } for i in combined_nodes
    ]
)

ecosphere_flows = {}
for item in ecosphere_flows_mapping.keys():
    ecosphere_flows[str(uuid.uuid4())] = {
        'name': ecosphere_flows_mapping[item]['name'],
        'unit': ecosphere_flows_mapping[item]['unit'],
        'chemical_formula': ecosphere_flows_mapping[item]['chemical_formula'],
        'CAS': ecosphere_flows_mapping[item]['CAS'],
        'compartments': ecosphere_flows_mapping[item]['compartments'],
        'synonyms': ecosphere_flows_mapping[item]['synonyms'],
        'database_code': item,
        'type': 'biosphere',
    }


df_lookup_extension = pd.DataFrame(
    [
        {
            'uuid': i,
            'flow_id': ecosphere_flows[i]['database_code'],
        } for i in ecosphere_flows.keys()
    ]
)



# %%

import networkx as nx
import uuid



A = nx.MultiDiGraph(
    incoming_graph_data=None,   
)

nodes_production = {}
for node_dict in combined_nodes:
    nodes_production[node_dict['uuid']] = {
        "name": node_dict['process']["name"],
        "product": node_dict['product']["name"],
        "unit": node_dict['product']["unit"],
        "database_code_process": node_dict['process']["id"],
        "database_code_product": node_dict['product']["id"],
        "geography": node_dict['process']["geography"],
        "type": node_dict['type'],
    }

for node_id, attributes in nodes_production.items():
    A.add_node(node_id, **attributes)


edges_production = [edge for edge in technosphere_edges if edge.positive==False]
df_edges = pd.DataFrame([(edge.source, edge.target, edge.amount) for edge in edges_production], columns=['product_id', 'process_id', 'amount'])

df_uuid = df_edges.merge(
    df_lookup_production[['uuid', 'process_id']],
    on=['process_id'],
    how='left'
)
df_uuid['process_id'] = df_uuid['uuid']
df_uuid = df_uuid.drop(columns=['uuid'])

df_uuid = df_uuid.merge(
    df_lookup_production[['uuid', 'product_id']],
    on=['product_id'],
    how='left'
)
df_uuid['product_id'] = df_uuid['uuid']
df_uuid = df_uuid.drop(columns=['uuid'])


A.add_edges_from(ebunch_to_add=df_uuid.values.tolist())


# %%

B = nx.MultiDiGraph(
    incoming_graph_data=None,   
)

for node_id, attributes in ecosphere_flows.items():
    B.add_node(node_id, **attributes)

df_edges_bio = pd.DataFrame([(edge.process, edge.flow, edge.amount) for edge in ecosphere_edges], columns=['process_id', 'flow_id', 'amount'])

df_uuid_bio = df_edges_bio.merge(
    df_lookup_production[['uuid', 'process_id']],
    on=['process_id'],
    how='left'
)
df_uuid_bio['process_id'] = df_uuid_bio['uuid']
df_uuid_bio = df_uuid_bio.drop(columns=['uuid'])

df_uuid_bio = df_uuid_bio.merge(
    df_lookup_extension[['uuid', 'flow_id']],
    on=['flow_id'],
    how='left'
)
df_uuid_bio['flow_id'] = df_uuid_bio['uuid']
df_uuid_bio = df_uuid_bio.drop(columns=['uuid'])

B.add_edges_from(ebunch_to_add=list(df_uuid_bio.values))

# %%

BcomposeA = nx.compose(B, A)


# %%
# troubleshooting biosphere flows

len(set(ecosphere_flows.keys())) # 4329
len(set(edge.flow for edge in ecosphere_edges)) # 2100

set(ecosphere_flows_mapping.keys()).issuperset(set(edge.flow for edge in ecosphere_edges)) # True
set(ecosphere_flows.keys()).issuperset(set(df_uuid_bio['flow_id'])) # True
