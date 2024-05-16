from json import load
from pathlib import Path

import flask
from dash import Dash, Input, Output, callback, dcc, html
from pandas import read_csv

from statistics_server.layout import grouping_dropdown, year_range_slider
from statistics_server.simple_graph import create_line_graph_figure

# TODO: remove hardcoding
variable_name = "years_injob"
variable_type = "numerical"

data_base_test_path = Path(".").joinpath("tests/test_data/").absolute()
group_metadata_file = data_base_test_path.joinpath("group_metadata.json").absolute()

data_test_path = data_base_test_path.joinpath(
    f"{variable_type}/{variable_name}/"
).absolute()
data_test_file = data_test_path.joinpath(f"{variable_name}_year.csv").absolute()
variable_metadata_file = data_test_path.joinpath("meta.json")

with open(variable_metadata_file, "r", encoding="utf-8") as file:
    variable_metadata = load(file)


data_test_frame = read_csv(data_test_file)

# TODO: End remove hardcoding

server = flask.Flask(__name__)
app = Dash(__name__, server=server)  # type: ignore

with open(group_metadata_file, "r", encoding="utf-8") as file:
    metadata = load(file)

app.layout = html.Div(
    id="outer-container",
    children=[
        year_range_slider(variable_metadata["start_year"], variable_metadata["end_year"]),
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
                    ],
                ),
                dcc.Graph(
                    id="graph",
                    className="graph-container",
                    figure=create_line_graph_figure(data_test_frame, group=[]),
                ),
            ],
        ),
        dcc.Checklist(id="control-panel-checkbox", options=["Hide Control Panel"]),
    ],
)


@callback(
    Output("graph", "figure"),
    Output("second-group", "value"),
    Output("second-group", "options"),
    Input("first-group", "value"),
    Input("second-group", "value"),
    Input("first-group", "options"),
    prevent_initial_call=True,
)
def handle_dropdown(first_group, second_group, first_group_options):
    grouping = []
    if first_group == second_group:
        second_group = None

    if first_group:
        grouping.append(first_group)
    if second_group:
        grouping.append(second_group)
    grouping.sort()
    grouping_string = "_".join(grouping)
    data_file = data_test_path.joinpath(
        f"{variable_name}_year_{grouping_string}.csv"
    ).absolute()
    _dataframe = read_csv(data_file)
    options = []

    for option in first_group_options:
        if option["value"] is not None and option["value"] == first_group:
            continue
        options.append(option)
    return create_line_graph_figure(_dataframe, group=grouping), second_group, options


def run():
    app.run_server(debug=True)


application = app.run_server


if __name__ == "__main__":
    app.run_server(debug=True)
