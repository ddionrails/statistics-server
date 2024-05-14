from pathlib import Path

import flask
from dash import Dash, html
from json import load

from statistics_server.layout import grouping_dropdown, year_range_slider

group_test_file = Path(".").joinpath("tests/test_data/group_metadata.json").absolute()

server = flask.Flask(__name__)
app = Dash(__name__, server=server)  # type: ignore
with open(group_test_file, "r", encoding="utf-8") as file:
    metadata = load(file)

app.layout = html.Div(
    [
        "Hello World!",
        year_range_slider(1999, 2020),
        grouping_dropdown(metadata=metadata, element_id="test", language="de"),
    ]
)


def run():
    app.run_server(debug=False)


application = app.run_server


if __name__ == "__main__":
    app.run_server(debug=False)
