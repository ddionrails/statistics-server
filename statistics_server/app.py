from json import load
from pathlib import Path

from dash import Dash, Input, Output, callback, dcc, html
from flask import Flask, request
from pandas import read_csv
from plotly.graph_objects import Figure
from urllib.parse import parse_qs

from statistics_server.layout import grouping_dropdown, year_range_slider
from statistics_server.simple_graph import create_line_graph_figure

# TODO: remove hardcoding

data_base_test_path = Path(".").joinpath("tests/test_data/").absolute()
group_metadata_file = data_base_test_path.joinpath("group_metadata.json").absolute()

# TODO: End remove hardcoding

server = Flask(__name__)
app = Dash(__name__, server=server)  # type: ignore

with open(group_metadata_file, "r", encoding="utf-8") as file:
    metadata = load(file)

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
                        grouping_dropdown(
                            metadata=metadata, element_id="first-group", language="de"
                        ),
                        html.Div(
                            id="second-group-container",
                            children=[
                                grouping_dropdown(
                                    metadata=metadata,
                                    element_id="second-group",
                                    language="de",
                                ),
                            ],
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


@callback(
    Output("year-range-slider-container", "children"),
    Input("url", "search"),
)
def update_range_slider():
    if search[0] == "?":
        search = search[1:]
    parsed_search = parse_qs(search)
    variable_name = parsed_search["variable"][0]
    variable_type = parsed_search["type"][0]
    data_base_path = get_file_names(variable_type, variable_name)

    variable_metadata_file_path = data_base_path.joinpath("meta.json")
    with open(variable_metadata_file_path, "r", encoding="utf-8") as file:
        variable_metadata = load(file)

    return (
        year_range_slider(variable_metadata["start_year"], variable_metadata["end_year"]),
    )


@callback(
    Output("graph", "figure"),
    Output("second-group", "value"),
    Output("second-group", "options"),
    Input("url", "search"),
    Input("first-group", "value"),
    Input("second-group", "value"),
    Input("first-group", "options"),
    Input("confidence-checkbox", "value"),
)
def handle_inputs(
    search, first_group, second_group, first_group_options, show_confidence
):
    if search[0] == "?":
        search = search[1:]
    parsed_search = parse_qs(search)
    variable_name = parsed_search["variable"][0]
    variable_type = parsed_search["type"][0]
    data_base_path = get_file_names(variable_type, variable_name)

    grouping, options = handle_grouping(first_group, second_group, first_group_options)
    data_file = data_base_path.joinpath(
        "_".join([variable_name, "year", *grouping]) + ".csv"
    ).absolute()
    _dataframe = read_csv(data_file)
    measure = "mean"
    if variable_type == "categorical":
        grouping.append(variable_name)
        measure = "proportion"

    return (
        create_line_graph_figure(
            _dataframe,
            group=grouping,
            show_confidence=bool(show_confidence),
            measure=measure,
        ),
        second_group,
        options,
    )


def get_file_names(variable_type, variable_name):

    data_base_path = data_base_test_path.joinpath(
        f"{variable_type}/{variable_name}/"
    ).absolute()

    return data_base_path


def handle_grouping(first_group, second_group, first_group_options):

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


def run():
    app.run_server(debug=True)


application = app.run_server


if __name__ == "__main__":
    app.run_server(debug=True)
