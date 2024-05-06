"""Modular assembling of html layout."""

from enum import Enum
from typing import Generator, Literal, Union

from dash import dcc
from plotly.graph_objects import Figure

from statistics_server.types import PlotType

type COLOR = str

COLOR_PALETTE: tuple[COLOR, ...] = (
    "rgb(255, 194, 10)",
    "rgb(12, 123, 220)",
    "rgb(243, 203, 166)",
    "rgb(51, 61, 112)",
    "rgb(80, 253, 240)",
    "rgb(183, 90, 96)",
    "rgb(34, 148, 37)",
    "rgb(118, 118, 239)",
    "rgb(124, 101, 145)",
    "rgb(201, 148, 184)",
    "rgb(131, 231, 81)",
    "rgb(105, 144, 57)",
    "rgb(105, 170, 78)",
    "rgb(234, 88, 74)",
    "rgb(244, 186, 35)",
    "rgb(160, 22, 102)",
    "rgb(175, 31, 83)",
    "rgb(59, 66, 156)",
    "rgb(157, 159, 9)",
    "rgb(199, 161, 75)",
    "rgb(175, 186, 123)",
)

type LineType = (
    Literal["solid"]
    | Literal["dot"]
    | Literal["dash"]
    | Literal["longdash"]
    | Literal["dashdot"]
    | Literal["longdashdot"]
)

LINE_TYPES: tuple[LineType, ...] = (
    "solid",
    "dot",
    "dash",
    "longdash",
    "dashdot",
    "longdashdot",
)


class LineTypes(Enum):
    solid = 1
    dot = 2
    dash = 3
    longdash = 4
    dashdot = 5
    longdashdot = 6


def y_label_intervals(y_max: int):
    if y_max <= 20:
        return 1
    if y_max <= 50:
        return 5
    if y_max <= 200:
        return 10
    if y_max <= 500:
        return 50
    return 100


def get_colors_from_palette() -> Generator[COLOR, None, None]:
    """Returns all colors of the color palette, then starts over to return duplicates

    Colors were selected to be distinguishable for people
    with protanopia, deuteranopia or tritanopia.
    See https://davidmathlogic.com/colorblind for more information.
    """
    while True:
        for color in COLOR_PALETTE:
            yield color


def get_line_types() -> Generator[LineType, None, None]:
    """Returns and repeats all possible plotly line types."""
    while True:
        for line_type in LINE_TYPES:
            yield line_type


LABEL_KEY: dict[str, Union[Literal["label"], Literal["label_de"]]] = {
    "en": "label",
    "de": "label_de",
}
UNSELECTED_VALUE = {
    "en": {"label": "No Grouping", "value": None},
    "de": {"label": "Keine Gruppierung", "value": None},
}

PLOT_LANGUAGE_LABELS = {
    "en": {
        "lower_confidence": "Lower confidence",
        "upper_confidence": "Upper confidence",
    },
    "de": {
        "lower_confidence": "Untere Konfidenz Grenze",
        "upper_confidence": "Obere Konfidenz Grenze",
    },
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


def style_numeric_figure(
    figure: Figure, start_year: int, y_max: int, plot_type: PlotType
) -> None:
    """Mutate figure to customize styling"""
    if plot_type == "line":
        figure.update_traces(connectgaps=True)
    figure.update_layout(
        xaxis={"tickmode": "linear", "tick0": start_year, "dtick": 1},
        yaxis={"tickmode": "linear", "tick0": 0, "dtick": y_label_intervals(y_max)},
        hoverlabel=dict(font_size=16, font_family="Rockwell"),
    )
    figure.update_yaxes(showline=True, rangemode="tozero", linewidth=1, linecolor="black")
    figure.update_xaxes(showline=True, linewidth=1, linecolor="black")
