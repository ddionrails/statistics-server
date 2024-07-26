from os import getenv
from pathlib import Path

import yaml
from pandas import DataFrame

from statistics_server.types import VariableMetadata

UI_TRANSLATION_KEY = "UI_TRANSLATIONS_PATH"

YEAR_TRANSLATION = {"en": "Year", "de": "Jahr"}

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


def switch_label_language(data: DataFrame, metadata: list[VariableMetadata]):

    label_mapping: dict[str, dict[str, str]] = {}
    for variable_metadata in metadata:
        variable = variable_metadata["variable"]
        label_mapping[variable] = {}
        for label, label_de, value in zip(
            variable_metadata["value_labels"],
            variable_metadata["value_labels_de"],
            variable_metadata["values"],
        ):
            if value < 0:
                continue
            label_mapping[variable][label] = label_de
    return data.replace(label_mapping)
