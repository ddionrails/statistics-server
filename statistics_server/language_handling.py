from os import getenv
from pathlib import Path

import yaml

UI_TRANSLATION_KEY = "UI_TRANSLATIONS_PATH"

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
