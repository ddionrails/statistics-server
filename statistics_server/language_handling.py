from os import getenv
from pathlib import Path

import yaml
from pandas import DataFrame
from pandas.api.types import CategoricalDtype

from statistics_server.types import VariableMetadata

UI_TRANSLATION_KEY = "UI_TRANSLATIONS_PATH"

YEAR_TRANSLATION = {"en": "Year", "de": "Jahr"}
MEASURE_TRANSLATION = {
    "en": {"mean": "Mean", "median": "Median", "proportion": "Proportion"},
    "de": {"mean": "Durchschnitt", "median": "Median", "proportion": "Anteil"},
}

UI_TRANSLATIONS_CONFIG_PATH = Path(getenv(UI_TRANSLATION_KEY, ""))
if UI_TRANSLATIONS_CONFIG_PATH == Path("") or not UI_TRANSLATIONS_CONFIG_PATH.exists():
    raise RuntimeError(
        (
            "UI translation config not properly set. "
            f"Set {UI_TRANSLATION_KEY} environment variable to an existing Path of."
        )
    )


def get_language_config(language: str = "en"):
    with open(UI_TRANSLATIONS_CONFIG_PATH, "r", encoding="utf-8") as file:
        language_config = yaml.load(file, yaml.CLoader)
    return language_config[language]


def handle_categorical_labels_and_order(
    data: DataFrame, metadata: list[VariableMetadata], language="de"
):
    """Order columns by metadata and switch labels to language

    Labels in metadata are in an ordered list.
    The order in the list corresponds to an ordered list for the codes.
    This means that the labels will be indirectly ordered by the variable codes.
    """

    label_mapping: dict[str, dict[str, str]] = {}
    type_mapping: dict[str, list[str]] = {}
    for variable_metadata in metadata:
        variable = variable_metadata["variable"]
        type_mapping[variable] = []
        label_mapping[variable] = {}
        for label, label_de, value in zip(
            variable_metadata["value_labels"],
            variable_metadata["value_labels_de"],
            variable_metadata["values"],
        ):
            if value < 0:
                continue
            if language == "de":
                type_mapping[variable].append(label_de)
                label_mapping[variable][label] = label_de
                continue
            type_mapping[variable].append(label)
            label_mapping[variable][label] = label
    data = data.replace(label_mapping)
    for variable, order in type_mapping.items():
        _type = CategoricalDtype(categories=order, ordered=True)
        data[variable] = data[variable].astype(_type)
    data = data.sort_values(["year", *list(type_mapping.keys())])
    return data
