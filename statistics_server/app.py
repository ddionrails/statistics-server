from json import load
from os import getenv
from pathlib import Path
from typing import cast, get_args
from urllib.parse import parse_qs

from dash import Dash, Input, Output, callback, dcc, html
from flask import Flask
from pandas import read_csv
from plotly.graph_objects import Figure

from statistics_server.layout import (
    create_grouping_dropdown,
    create_measure_dropdown,
    year_range_slider,
)
from statistics_server.names import MEAN, PROPORTION, YEAR
from statistics_server.simple_graph import create_line_graph_figure
from statistics_server.types import Measure, PlotlyLabeledOption, VariableType


def get_environment_variables():
    base_path_env_variable = getenv("STATISTICS_BASE_PATH")
    if not base_path_env_variable:
        raise EnvironmentError("STATISTICS_BASE_PATH environment variable not set.")
    return Path(base_path_env_variable).absolute()


data_base_path = get_environment_variables()
group_metadata_file = data_base_path.joinpath("group_metadata.json").absolute()

server = Flask(__name__)
app = Dash(__name__, server=server)  # type: ignore

with open(group_metadata_file, "r", encoding="utf-8") as metadata_file:
    metadata = load(metadata_file)

app.layout = html.Div(
    id="outer-container",
    children=[
        html.Div(id="year-range-slider-container", children=[]),
        html.Div(
            id="control-and-graph",
            children=[
                html.Div(
                    className="control-panel",
                    children=[
                        create_grouping_dropdown(
                            metadata=metadata, element_id="first-group", language="de"
                        ),
                        html.Div(
                            id="second-group-container",
                            children=[
                                create_grouping_dropdown(
                                    metadata=metadata,
                                    element_id="second-group",
                                    language="de",
                                ),
                            ],
                        ),
                        html.Div(id="measure-dropdown-container"),
                        dcc.Checklist(
                            id="confidence-checkbox",
                            options=[
                                {
                                    "label": "Show Confidence Interval",
                                    "value": "confidence",
                                },
                            ],
                            value=["confidence"],
                        ),
                    ],
                ),
                dcc.Graph(
                    id="graph",
                    className="graph-container",
                    figure=Figure(),
                ),
            ],
        ),
        dcc.Checklist(id="control-panel-checkbox", options=["Hide Control Panel"]),
        dcc.Location(id="url"),
    ],
)


def _ensure_correct_variable_type(variable_type: str) -> VariableType:
    if variable_type in get_args(VariableType.__value__):
        return cast(VariableType, variable_type)
    raise RuntimeError("Non-existent variable type selected.")


@callback(
    Output("year-range-slider-container", "children"),
    Input("url", "search"),
)
def update_range_slider(search: str) -> dcc.RangeSlider:
    if search[0] == "?":
        search = search[1:]
    parsed_search = parse_qs(search)
    variable_name = parsed_search["variable"][0]
    variable_type = _ensure_correct_variable_type(parsed_search["type"][0])

    data_base_path = get_variable_data_path(variable_type, variable_name)

    variable_metadata_file_path = data_base_path.joinpath("meta.json")
    with open(variable_metadata_file_path, "r", encoding="utf-8") as file:
        variable_metadata = load(file)

    return year_range_slider(
        variable_metadata["start_year"], variable_metadata["end_year"]
    )


def parse_search(raw_search: str) -> tuple[str, VariableType]:
    if not raw_search:
        raise RuntimeError("Incorrect query parameters provided.")

    if raw_search[0] == "?":
        search = raw_search[1:]

    parsed_search = parse_qs(search)

    if not ("type" in parsed_search and "variable" in parsed_search):
        raise RuntimeError("Incorrect query parameters provided.")

    variable_type = _ensure_correct_variable_type(parsed_search["type"][0])
    variable_name = parsed_search["variable"][0]

    return variable_name, variable_type


@callback(
    Output("measure-dropdown-container", "children"),
    Input("url", "search"),
)
def handle_measure_dropdown(search: str) -> dcc.Dropdown | html.Div:
    """Create measure dropdown for numerical view or placeholder Div for other."""
    _measure_dropdown = html.Div(id="measure-dropdown")
    variable_type: VariableType
    _, variable_type = parse_search(search)
    if variable_type == "numerical":
        _measure_dropdown = create_measure_dropdown()
    return _measure_dropdown


@callback(
    Output("graph", "figure"),
    Output("first-group", "value"),
    Output("second-group", "options"),
    Input("url", "search"),
    Input("first-group", "value"),
    Input("second-group", "value"),
    Input("first-group", "options"),
    Input("confidence-checkbox", "value"),
    Input("year-range-slider", "value"),
    Input("measure-dropdown", "value"),
)
def handle_inputs(
    search: str,
    first_group_value: str,
    second_group_value: str,
    first_group_options: list[PlotlyLabeledOption],
    show_confidence: str,
    year_range: tuple[int, int],
    measure: Measure,
) -> tuple[Figure, str, list[PlotlyLabeledOption]]:
    variable_name, variable_type = parse_search(search)
    data_base_path = get_variable_data_path(variable_type, variable_name)

    grouping, options = handle_grouping(
        first_group_value, second_group_value, first_group_options
    )
    data_file = data_base_path.joinpath(
        "_".join([variable_name, YEAR, *grouping]) + ".csv"
    ).absolute()
    _dataframe = read_csv(data_file)
    _dataframe = _dataframe[_dataframe[YEAR].between(*year_range)]

    if variable_type == "categorical":
        grouping.append(variable_name)
        measure = PROPORTION

    if measure == "":
        measure = MEAN

    return (
        create_line_graph_figure(
            _dataframe,
            group=grouping,
            show_confidence=bool(show_confidence),
            measure=measure,
        ),
        second_group_value,
        options,
    )


def get_variable_data_path(variable_type: VariableType, variable_name: str) -> Path:

    variable_data_base_path = data_base_path.joinpath(
        f"{variable_type}/{variable_name}/"
    ).absolute()

    return variable_data_base_path


def handle_grouping(
    first_group: str | None,
    second_group: str | None,
    first_group_options: list[PlotlyLabeledOption],
) -> tuple[list[str], list[PlotlyLabeledOption]]:

    grouping = []
    if first_group == second_group:
        second_group = None

    if first_group:
        grouping.append(first_group)
    if second_group:
        grouping.append(second_group)
    grouping.sort()
    options = []

    for option in first_group_options:
        if option["value"] is not None and option["value"] == first_group:
            continue
        options.append(option)

    return grouping, options


def run() -> None:
    app.run(debug=False)


application = app.run


if __name__ == "__main__":
    app.run(debug=False)
