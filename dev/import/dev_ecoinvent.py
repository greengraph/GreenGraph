# based on
# https://github.com/cmutel/spatial-assessment-blog/blob/master/notebooks/How%20to%20use%20ecoinvent.ipynb

# %%
from pathlib import Path
import networkx as nx

RELEASE_PATH = Path("/Users/michaelweinold/data/ecoinvent 3.7.1_apos_ecoSpold02")

from lxml import objectify

NS = "{http://www.EcoInvent.org/EcoSpold02}"

ACTIVITIES_FP = RELEASE_PATH / "MasterData" / "ActivityIndex.xml"
GEOGRAPHIES_FP = RELEASE_PATH / "MasterData" / "Geographies.xml"
ACTIVITY_NAME_FP = RELEASE_PATH / "MasterData" / "ActivityNames.xml"

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

PRODUCTS_FP = RELEASE_PATH / "MasterData" / "IntermediateExchanges.xml"

def maybe_missing(
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
        "comment": maybe_missing(elem, "comment"),
        "product_information": maybe_missing(elem, "productInformation", True),
        "classifications": dict(
            [
                (c.classificationSystem.text, c.classificationValue.text)
                for c in elem.iterchildren(NS + "classification")
            ]
        ),
    }
    for elem in objectify.parse(open(PRODUCTS_FP)).getroot().iterchildren()
}

FLOWS_FP = RELEASE_PATH / "MasterData" / "ElementaryExchanges.xml"

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

import hashlib

_ = lambda str: str.encode("utf-8")


def unique_identifier(process_dict: dict, product_dict: dict, type: str) -> str:
    return hashlib.md5(
        _(process_dict["name"])
        + _(product_dict["name"])
        + _(product_dict["unit"])
        + _(process_dict["geography"])
        + _(type)
    ).hexdigest()


from dataclasses import dataclass

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

import pyecospold
from pyecospold.model_v2 import IntermediateExchange, Activity, FlowData

process_nodes, product_nodes = {}, {}
technosphere_edges, ecosphere_edges = [], []
INPUTS = ("Materials/Fuels", "Electricity/Heat", "Services", "From Technosphere (unspecified)")


def get_process_id(edge: IntermediateExchange, activity: Activity) -> str:
    return edge.activityLinkId or activity.id


def reference_product(flows: FlowData) -> str:
    candidates = [
        edge for edge in flows.intermediateExchanges
        if edge.groupStr == "ReferenceProduct"
        and edge.amount != 0
    ]
    if not len(candidates) == 1:
        raise ValueError("Can't find reference product")
    return candidates[0].intermediateExchangeId

from tqdm import tqdm

for filepath in tqdm((RELEASE_PATH / "datasets").iterdir()):
    if not filepath.name.endswith(".spold"):
        continue
    ecospold = pyecospold.parse_file_v2(filepath)
    activity = ecospold.activityDataset.activityDescription.activity[0]

    this_process = activity_mapping[activity.id]
    this_product = product_mapping[reference_product(ecospold.activityDataset.flowData)]

    this_process_id = unique_identifier(this_process, this_product, "process")
    this_product_id = unique_identifier(this_process, this_product, "product")

    process_nodes[this_process_id] = (this_process, this_product)
    product_nodes[this_product_id] = (this_process, this_product)

    for edge in ecospold.activityDataset.flowData.intermediateExchanges:
        if not edge.amount:
            continue

        other_process = activity_mapping[get_process_id(edge=edge, activity=activity)]
        other_product = product_mapping[edge.intermediateExchangeId]
        other_product_id = unique_identifier(other_process, other_product, "product")

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

    # why are these empty?
    for edge in ecospold.activityDataset.flowData.elementaryExchanges:
        ecosphere_edges.append(EcosphereEdge(
            flow=edge.elementaryExchangeId,
            process=this_process_id,
            amount=edge.amount
        ))

# %%
# kind of works

import pandas

characterization_factors = pandas.read_excel(
    '/Users/michaelweinold/data/ecoinvent 3.11_LCIA_implementation/LCIA Implementation 3.11.xlsx', sheet_name="CFs"
)
characterization_units = pandas.read_excel(
    '/Users/michaelweinold/data/ecoinvent 3.11_LCIA_implementation/LCIA Implementation 3.11.xlsx', sheet_name="Indicators"
)

@dataclass
class CharacterizationFactor:
    flow: str
    amount: float


lcia_reverse_mapping = {
    (v['name'],) + tuple(v["compartments"]): k
    for k, v in ecosphere_flows_mapping.items()
}

impact_categories = {
    tuple(obj[:3]): {
        'cfs': []
    }
    for obj in characterization_factors.values.tolist()
}

for obj in characterization_factors.values.tolist():
    impact_categories[tuple(obj[:3])]['cfs'].append(
        CharacterizationFactor(
            flow=lcia_reverse_mapping[tuple(obj[3:6])],
            amount=obj[6]
        )
    )

for obj in characterization_factors.values.tolist():
    impact_categories[tuple(obj[:3])]['unit'] = obj[3]