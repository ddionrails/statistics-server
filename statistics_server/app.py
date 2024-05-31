from json import load
from os import getenv
from pathlib import Path
from typing import Any, cast, get_args
from urllib.parse import parse_qs

from dash import Dash, Input, Output, callback, dcc, dependencies, html
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


PLACEHOLDER_MEASURE_DROPDOWN = dcc.Dropdown([MEAN], MEAN, id="measure-dropdown")
PLACEHOLDER_YEAR_RANGE_SLIDER = dcc.RangeSlider(1, 2, id="year-range-slider")

data_base_path = get_environment_variables()
group_metadata_file = data_base_path.joinpath("group_metadata.json").absolute()

server = Flask(__name__)
app = Dash(__name__, server=server)  # type: ignore

with open(group_metadata_file, "r", encoding="utf-8") as metadata_file:
    metadata = load(metadata_file)

app.layout = html.Div(
    id="outer-container",
    children=[
        html.Div(
            id="year-range-slider-container",
            children=[PLACEHOLDER_YEAR_RANGE_SLIDER],
        ),
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
                        html.Div(
                            id="measure-dropdown-container",
                            children=[PLACEHOLDER_MEASURE_DROPDOWN],
                        ),
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
                        dcc.Checklist(
                            id="legend-checkbox",
                            options=[
                                {
                                    "label": "Show Legend",
                                    "value": "legend",
                                },
                            ],
                            value=["legend"],
                        ),
                        html.Button("Download CSV", id="btn-data-download"),
                        dcc.Download(id="data-download", type="str"),
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
    Output("data-download", "data"),
    dependencies.State("url", "search"),
    dependencies.State("first-group", "value"),
    dependencies.State("second-group", "value"),
    dependencies.State("first-group", "options"),
    dependencies.State("year-range-slider", "value"),
    Input("btn-data-download", "n_clicks"),
    prevent_initial_call=True,
)
def download(
    search: str,
    first_group_value: str,
    second_group_value: str | None,
    first_group_options: list[PlotlyLabeledOption],
    year_range: tuple[int, int],
    _,
) -> dict[str, Any | None] | None:

    variable_name, variable_type = parse_search(search)
    data_base_path = get_variable_data_path(variable_type, variable_name)

    grouping, _, second_group_value = handle_grouping(
        first_group_value, second_group_value, first_group_options
    )
    file_name_base = "_".join([variable_name, YEAR, *grouping])
    data_file = data_base_path.joinpath(file_name_base + ".csv").absolute()
    _dataframe = read_csv(data_file)

    _dataframe = _dataframe[_dataframe[YEAR].between(*year_range)]

    download_file_name = (
        "_".join([file_name_base, *[str(i) for i in year_range]]) + ".csv"
    )

    return dcc.send_data_frame(_dataframe.to_csv, download_file_name, index=False)


@callback(
    Output("graph", "figure"),
    Output("second-group", "value"),
    Output("second-group", "options"),
    Input("first-group", "value"),
    Input("second-group", "value"),
    Input("first-group", "options"),
    Input("confidence-checkbox", "value"),
    Input("legend-checkbox", "value"),
    Input("year-range-slider", "value"),
    Input("measure-dropdown", "value"),
    dependencies.State("url", "search"),
    dependencies.State("graph", "figure"),
)
def handle_inputs(
    first_group_value: str,
    second_group_value: str | None,
    first_group_options: list[PlotlyLabeledOption],
    show_confidence: str,
    show_legend: str,
    year_range: tuple[int, int],
    measure: Measure,
    search: str,
    current_graph,
) -> tuple[Figure, str | None, list[PlotlyLabeledOption]]:

    trace_visibility = {}
    if current_graph:
        trace_visibility = {
            trace["name"]: trace.get("visible", True) for trace in current_graph["data"]
        }

    variable_name, variable_type = parse_search(search)
    data_base_path = get_variable_data_path(variable_type, variable_name)

    grouping, options, second_group_value = handle_grouping(
        first_group_value, second_group_value, first_group_options
    )
    data_file = data_base_path.joinpath(
        "_".join([variable_name, YEAR, *grouping]) + ".csv"
    ).absolute()
    _dataframe = read_csv(data_file)

    if year_range:
        _dataframe = _dataframe[_dataframe[YEAR].between(*year_range)]

    if variable_type == "categorical":
        # It is currently important that variable name is at the end of the grouping list
        # for the grouping of the bar plot to work properly.
        grouping.append(variable_name)
        measure = PROPORTION

    if not measure:
        measure = MEAN

    return (
        create_line_graph_figure(
            _dataframe,
            group=grouping,
            show_confidence=bool(show_confidence),
            show_legend=bool(show_legend),
            measure=measure,
            trace_visibility=trace_visibility,
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
) -> tuple[list[str], list[PlotlyLabeledOption], str | None]:

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

    return grouping, options, second_group


def run() -> None:
    app.run(debug=False)


application = app.run


if __name__ == "__main__":
    app.run(debug=False)
