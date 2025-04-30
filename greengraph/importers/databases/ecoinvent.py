import hashlib
from lxml import objectify
from dataclasses import dataclass
import pyecospold
from pyecospold.model_v2 import IntermediateExchange, Activity, FlowData
from pathlib import Path
from greengraph.utility.logging import logtimer




def _extract_ecospold_xml_files(path: Path) -> dict:
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

    dict_mapping = _extract_ecospold_xml_masterdata_files(path=path)
    activity_mapping = dict_mapping['activity_mapping']
    product_mapping = dict_mapping['product_mapping']

    INPUTS = ("Materials/Fuels", "Electricity/Heat", "Services", "From Technosphere (unspecified)")

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
            "process_nodes": process_nodes,
            "product_nodes": product_nodes,
            "ecosphere_flows_mapping": ecosphere_flows_mapping,
            "technosphere_edges": technosphere_edges,
            "ecosphere_edges": ecosphere_edges,
        }


def _prepare_ecoinvent_node_and_edge_lists(
    process_nodes: dict,
    product_nodes: dict,
    ecosphere_flows_mapping: dict,
    technosphere_edges: list,
    ecosphere_edges: list,
) -> dict:
    r"""
    Given a dictionary of process nodes, product nodes, ecosphere flows mapping,
    technosphere edges, and ecosphere edges, this function prepares the data
    for further processing.

    Notes
    -----

    - `process_nodes`

    Dictionary, where:

    | Element | Description                                                                                                                                                |
    | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | key     | A unique identifier string for the **process**, *generated by the EcoSpold importer.*                                                                      |
    | value   | Tuple, where the first element is a dictionary containing the process attributes and the second element is a dictionary containing the product attributes. |

    ```python
    {
        (...)
        'c0a2b9e0cb079e8f9274a96e864a312d': (
            {
                'name': 'treatment of sludge from pulp and paper production, sanitary landfill',
                'geography': 'Rest-of-World',
                'start': '1994-01-01',
                'end': '2020-12-31',
                'type': 'ordinary transforming activity (default)'
            },
            {
                'name': 'sludge from pulp and paper production',
                'unit': 'kg',
                'comment': '',
                'product_information': '',
                'classifications': 
                {
                    'By-product classification': 'Waste',
                    'CPC': '39920: Sewage sludge'
                }
            }
        ),
        (...)
    }
    ```

    - `product_nodes`

    Dictionary, where:

    | Element | Description                                                                                                                                                |
    | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | key     | A unique identifier string for the **product**, *generated by the EcoSpold importer.*                                                                      |
    | value   | Tuple, where the first element is a dictionary containing the process attributes and the second element is a dictionary containing the product attributes. |

    ```python
    {
        (...)
        'd243553fcd4f39f844a92d7389fabb36': (
            {
                'name': 'treatment of sludge from pulp and paper production, sanitary landfill',
                'geography': 'Rest-of-World',
                'start': '1994-01-01',
                'end': '2020-12-31',
                'type': 'ordinary transforming activity (default)'
            },
            {
                'name': 'sludge from pulp and paper production',
                'unit': 'kg',
                'comment': '',
                'product_information': '',
                'classifications':
                    {
                        'By-product classification': 'Waste',
                        'CPC': '39920: Sewage sludge'
                    }
            }
        ),
        (...)
    }
    ```

    - `ecosphere_flows_mapping`

    Dictionary, where:

    | Element | Description                                                                                           |
    | ------- | ----------------------------------------------------------------------------------------------------- |
    | key     | A unique identifier string for the **biosphere flow**, *taken directly from by the EcoSpold file*.    |
    | value   | Dictionary containing the attributes of the biosphere flow.                                           |

    ```python
    {
        (...)
        'e2d860e3-1038-4386-a5f1-25ad75d18bbd': {
            'name': '2-Methyl-1-propanol',
            'unit': 'kg',
            'chemical_formula': None,
            'CAS': '000078-83-1',
            'compartments': ['air', 'urban air close to ground'],
            'synonyms': ['Isobutanol, Isobutyl alcohol']
        },
        (...)
    }
    ```

    - `technosphere_edges`

    List containing `TechnosphereEdge` DataClasses, where:

    | Element  | Description                                                                     |
    | -------- | ------------------------------------------------------------------------------- |
    | source   | Edge source. Is either a `product_node` or a `process_node`.                    |
    | target   | Edge target. Is either a `product_node` or a `process_node`.                    |
    | amount   | The flow amount of the edge. Sign does not matter (because reasons?)            |
    | positive | Boolean indicating whether the flow is produced (`True`) or consumed (`False`). |

    ```python
    [
        (...)
        TechnosphereEdge(
            source='869b735bbc83a0688c17e0b546bd8feb',
            target='b702a9803e520af8512fbb2e78913059',
            amount=5.22330065113794e-07,
            positive=False
        ),
        (...)
    ]
    ```

    - `ecosphere_edges`

    List containing `EcosphereEdge` DataClasses, where:

    | Element  | Description                                                                    |
    | -------- | ------------------------------------------------------------------------------ |
    | flow     | The unique identifier of the ecosphere flow.                                   |
    | process  | The unique identifier of the process.                                          |
    | amount   | The flow amount of the edge.                                                   |

    ```python
    [
        (...)
        EcosphereEdge(
            flow='73b225ab-ddc4-4a38-9ed0-ceedee987424',
            process='777894b5211611f7f0be248a97ae635a',
            amount=0.00012818
        )
        (...)
    ]
    ```


    Warnings
    --------
    The EcoSpold parser uses a specific convention for production processes
    and the products they produce. In this convention, products are represented as nodes in the graph:

    ```mermaid
    graph LR
    A(("1"))
    B("P(1)")
    C(("2"))

    A --> B --> C

    classDef pNodeStyle fill:#ADD8E6,stroke:#333,stroke-width:1px
    class B pNodeStyle
    ```

    whereas in the current GreenGraph implementation,
    products are simply an attribute of process nodes:

    ```mermaid
    graph LR
    A(("1"))
    C(("2"))

    A -- P(1) --> C
    ```

    The `technosphere_edges` list returned by the EcoSpold parser therefore follows the convention:

    - If `positive==True`, the edge describes reference product production (always `abs(amount)==1.0`) and:

    | source         | target         |
    | -------------- | -------------- |
    | `product_node` | `process_node` |

    - If `positive==False`, the edge describes reference product consumption and:

    | source         | target         |
    | -------------- | -------------- |
    | `process_node` | `product_node` |


    Parameters
    ----------
    process_nodes : dict
        Dictionary containing process nodes.
    product_nodes : dict
        Dictionary containing product nodes.
    ecosphere_flows_mapping : dict
        Dictionary containing ecosphere flows mapping.
    technosphere_edges : list
        List of technosphere edges.
    ecosphere_edges : list
        List of ecosphere edges.

    Returns
    -------
    dict
        A dictionary containing prepared data for further processing.
    """

    # Nodes for production (technosphere)
    nodes_production = [
        {
            'type': 'technosphere',
            'name': process_attributes[0]['name'],
            'product': product_attributes[1]['name'],
            'unit': product_attributes[1]['unit'],
            'geography': process_attributes[0]['geography'],
            'classifications': product_attributes[1]['classifications'],
            'brightway_code_process': process_code,
            'brightway_code_product': product_code
        }
        for (process_code, process_attributes), (product_code, product_attributes) in zip(process_nodes.items(), product_nodes.items())
    ]

    # Nodes for extensions (biosphere)
    nodes_extension = [
        {
            'type': 'biosphere',
            'name': extension_attributes['name'],
            'unit': extension_attributes['unit'],
            'chemical_formula': extension_attributes['chemical_formula'],
            'CAS': extension_attributes['CAS'],
            'compartments': extension_attributes['compartments'],
            'synonyms': extension_attributes['synonyms'],
            'brightway_code_extension': extension_code
        }
        for extension_code, extension_attributes in ecosphere_flows_mapping.items()
    ]

    # Edges for biosphere
    edges_biosphere = [(edge.process, edge.flow, edge.amount) for edge in ecosphere_edges]

    # Edges for production (technosphere)
    product_to_process = {
        node['brightway_code_product']: node['brightway_code_process']
        for node in nodes_production
    }
    edges_production = [
        (product_to_process.get(edge.source, None), edge.target, float(edge.amount))
        for edge in technosphere_edges if not edge.positive
    ]

    return {
        'nodes_production': nodes_production,
        'nodes_extension': nodes_extension,
        'edges_biosphere': edges_biosphere,
        'edges_production': edges_production,
    }