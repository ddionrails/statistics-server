"""Modular assembling of html layout."""

from typing import Literal, Union

from dash import dcc

LABEL_KEY: dict[str, Union[Literal["label"], Literal["label_de"]]] = {
    "en": "label",
    "de": "label_de",
}
UNSELECTED_VALUE = {
    "en": {"label": "No Grouping", "value": None},
    "de": {"label": "Keine Gruppierung", "value": None},
}


def year_range_slider(start_year: int, end_year: int) -> dcc.Slider:
    """Create a year range Slider."""
    return dcc.Slider(
        start_year, end_year, step=1, value=[start_year, end_year], id="year-range-slider"
    )


def grouping_dropdown(metadata, element_id, exclude_value=None, language="en"):
    """Create a dropdown to select a group to group by."""
    if language != "de":
        language = "en"
    label = LABEL_KEY[language]
    default = UNSELECTED_VALUE[language]
    options = [default]

    for group in metadata["groups"]:
        if exclude_value == group["variable"]:
            continue
        options.append({"label": group[label], "value": group["variable"]})
    return dcc.Dropdown(options=options, value=default["value"], id=element_id)
