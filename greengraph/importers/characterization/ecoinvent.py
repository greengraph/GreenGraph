# %%

import pandas as pd

import pandas

characterization_factors = pandas.read_excel(
    LCIA_PATH / "LCIA_implementation_3.7.1.xlsx", sheet_name="CFs"
)
characterization_units = pandas.read_excel(
    LCIA_PATH / "LCIA_implementation_3.7.1.xlsx", sheet_name="units"
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