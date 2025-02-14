"""Modular assembling of html layout."""

from typing import Generator, Literal, Union

from dash import dcc
from plotly.graph_objects import Figure

from statistics_server.types import (
    GroupingMetadata,
    LanguageCode,
    Measure,
    PlotType,
    UITranslation,
    VariableMetadata,
)

type COLOR = str
FONT_FAMILY = "Helvetica"

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


def y_label_intervals(y_max: int):
    if y_max <= 2:
        return 0.1
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
UI_TRANSLATIONS: UITranslation = {
    "unselected_group": {
        "en": {"label": "No Grouping", "value": None},
        "de": {"label": "Keine Gruppierung", "value": None},
    },
    "measure_names": {
        "en": {"mean": "Mean"},
        "de": {"mean": "Durchschnitt"},
    },
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

DROPDOWN_PLACEHOLDER = {"en": "Select Group", "de": "Gruppierung Auswählen"}


def create_measure_dropdown(language="en"):
    measure_names = UI_TRANSLATIONS["measure_names"][language]
    options = [
        {"value": measure, "label": label} for measure, label in measure_names.items()
    ]

    return dcc.Dropdown(
        options,
        value="mean",
        id="measure-dropdown",
    )


def create_grouping_dropdown(
    metadata: dict[str, VariableMetadata],
    element_id: str,
    exclude_value: str = "",
    language: LanguageCode = "en",
    selected: str | None = None,
) -> dcc.Dropdown:
    """Create a dropdown to select a group to group by."""
    if language != "de":
        language = "en"
    label = LABEL_KEY[language]
    default = UI_TRANSLATIONS["unselected_group"][language]
    options: list[GroupingMetadata] = []
    selected_value = default["value"]

    for group in metadata.values():
        if exclude_value == group["variable"]:
            continue
        options.append({"label": group[label], "value": group["variable"]})
    if selected != default["value"]:
        selected_value = selected
    options.sort(key=lambda item: item["label"])
    options.insert(0, default)
    return dcc.Dropdown(
        options,
        value=selected_value,
        id=element_id,
        placeholder=DROPDOWN_PLACEHOLDER[language],
    )


def style_numeric_figure(
    figure: Figure,
    y_max: int,
    plot_type: PlotType,
    start_year: int | None = None,
    end_year: int | None = None,
    measure: Measure = "mean",
) -> None:
    """Mutate figure to customize styling"""
    if plot_type == "line":
        figure.update_traces(connectgaps=True)
    if plot_type == "bar":
        figure.update_layout(barmode="stack")
    yaxis_layout = {"tickmode": "linear", "tick0": 0}
    if measure in ("mean", "median"):
        yaxis_layout["dtick"] = y_label_intervals(y_max)
    if measure in "proportion":
        yaxis_layout["tickformat"] = ",.0%"
        yaxis_layout["dtick"] = 0.10  # [number / 100 for number in range(0, 100, 5)]
        yaxis_layout["range"] = [0, 1]

    figure.update_layout(
        xaxis={"tickmode": "linear", "tick0": start_year, "dtick": 1},
        yaxis=yaxis_layout,
        hoverlabel=dict(font_size=16, font_family=FONT_FAMILY),
        font_family=FONT_FAMILY,
    )

    figure.update_yaxes(showline=True, rangemode="tozero", linewidth=1, linecolor="black")

    if not plot_type == "bar" and start_year is not None and end_year is not None:
        figure.update_xaxes(
            showline=True,
            linewidth=1,
            linecolor="black",
            range=[start_year - 1, end_year + 1],
        )
