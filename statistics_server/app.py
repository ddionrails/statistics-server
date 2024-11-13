from json import load
from os import getenv, mkdir
from pathlib import Path
from shutil import make_archive
from tempfile import TemporaryDirectory
from typing import Any, cast, get_args
from urllib.parse import parse_qs

from dash import Dash, Input, Output, callback, dcc, dependencies, html
from flask import Flask
from pandas import read_csv
from plotly.graph_objects import Figure

from statistics_server.language_handling import (
    get_language_config,
    handle_categorical_labels_and_order,
)
from statistics_server.layout import create_grouping_dropdown, create_measure_dropdown
from statistics_server.names import MEAN, PROPORTION, YEAR
from statistics_server.numerical_boxplot_graph import create_numerical_boxplot_figure
from statistics_server.simple_graph import (
    create_bar_graph_figure,
    create_line_graph_figure,
)
from statistics_server.types import (
    LanguageCode,
    Measure,
    PlotlyLabeledOption,
    VariableType,
)

LANGUAGE_CONFIG = get_language_config()
FONT_AWESOME_COPYRIGHT_NOTICE = (
    "Font Awesome Free 6.4.2 by @fontawesome - https://fontawesome.com"
    "License - https://fontawesome.com/license/free"
    " (Icons: CC BY 4.0, Fonts: SIL OFL 1.1, Code: MIT License)"
    "Copyright 2023 Fonticons, Inc."
)
BOXPLOT_MIN_VALUE = 10


def get_environment_variables() -> tuple[Path, str]:
    base_path_env_variable = getenv("STATISTICS_BASE_PATH")
    _url_base_pathname = getenv("URL_BASE_PATHNAME", "/")
    if not base_path_env_variable:
        raise EnvironmentError("STATISTICS_BASE_PATH environment variable not set.")
    return Path(base_path_env_variable).absolute(), _url_base_pathname


PLACEHOLDER_MEASURE_DROPDOWN = dcc.Dropdown([MEAN], MEAN, id="measure-dropdown")

data_base_path, url_base_pathname = get_environment_variables()
group_metadata_file = data_base_path.joinpath("group_metadata.json").absolute()
citation_metadata_file = data_base_path.joinpath("citation.json").absolute()

server = Flask(__name__)
app = Dash(
    __name__,
    server=server,  # type: ignore
    url_base_pathname=url_base_pathname,
    external_stylesheets=[
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css"
    ],
)

with open(group_metadata_file, "r", encoding="utf-8") as metadata_file:
    metadata = load(metadata_file)
with open(citation_metadata_file, "r", encoding="utf-8") as metadata_file:
    citation = load(metadata_file)


def _get_variable_metadata(base_path: Path) -> dict[str, Any]:
    variable_metadata_file_path = base_path.joinpath("meta.json")
    with open(variable_metadata_file_path, "r", encoding="utf-8") as file:
        variable_metadata = load(file)
    return variable_metadata


def _filter_group_metadata(_metadata, variable_name, variable_type):
    _base_path = get_variable_data_path(
        variable_type=variable_type, variable_name=variable_name
    )
    variable_metadata = _get_variable_metadata(_base_path)
    groups = variable_metadata.get("groups")
    if not groups:
        return _metadata
    output = {}
    for group in groups:
        if group in _metadata:
            output[group] = _metadata[group]
    return output


app.layout = html.Div(
    id="outer-container",
    children=[
        html.Div(
            id="control-and-graph",
            children=[
                html.Div(
                    id="control-panel",
                    className="control-panel",
                    children=[
                        create_grouping_dropdown(
                            metadata=metadata,
                            element_id="first-group",
                            language="de",
                        ),
                        create_grouping_dropdown(
                            metadata=metadata,
                            element_id="second-group",
                            language="de",
                        ),
                        html.Div(
                            id="measure-dropdown-container",
                            children=[PLACEHOLDER_MEASURE_DROPDOWN],
                        ),
                        html.Div(
                            id="confidence-container",
                            children=[
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
                                html.Button(
                                    id="confidence-popover-button",
                                    className="info-icon",
                                    children=[html.I(className="fas fa-info-circle")],
                                    style={"padding-left": "0.3em", "font-size": "1.2em"},
                                    **{
                                        "data-copyright-notice": FONT_AWESOME_COPYRIGHT_NOTICE,
                                    },
                                ),
                                html.Div(
                                    id="confidence-popover",
                                    className="hidden",
                                    children=[LANGUAGE_CONFIG["confidence_interval"]],
                                ),
                            ],
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
                        dcc.Checklist(
                            id="bargraph-checkbox",
                            className="removed",
                            options=[
                                {
                                    "label": "Show Bar Graph",
                                    "value": "bar",
                                },
                            ],
                            value=False,
                        ),
                        dcc.Checklist(
                            id="boxplot-checkbox",
                            className="removed",
                            options=[
                                {
                                    "label": "Show Boxplot",
                                    "value": "boxplot",
                                },
                            ],
                            value=False,
                        ),
                        html.Span(
                            id="boxplot-flag",
                            key="boxplot-flag",
                            className="removed",
                            children="hide",
                        ),
                        html.Div(
                            id="download-button-container",
                            children=[
                                html.Button(
                                    "Download CSV",
                                    id="btn-data-download",
                                ),
                                dcc.Download(id="data-download", type="str"),
                                html.Button(
                                    "Download Figure",
                                    id="btn-image-download",
                                ),
                                dcc.Download(id="image-download", type="str"),
                            ],
                            className="download-buttons",
                        ),
                    ],
                ),
                html.Div(
                    id="graph-citation-container",
                    children=[
                        dcc.Graph(
                            id="graph",
                            className="graph-container",
                            figure=Figure(),
                        ),
                        html.P(
                            id="citation-text",
                            children=["Cite as: ", citation["base_citation"]["en"]],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            id="below-control-and-graph",
            children=[],
        ),
        dcc.Location(id="url"),
    ],
)


def _ensure_correct_variable_type(variable_type: str) -> VariableType:
    if variable_type in get_args(VariableType.__value__):
        return cast(VariableType, variable_type)
    raise RuntimeError("Non-existent variable type selected.")


def parse_search(raw_search: str) -> tuple[str, VariableType, LanguageCode]:
    if not raw_search:
        raise RuntimeError("Incorrect query parameters provided.")

    search = raw_search
    if raw_search[0] == "?":
        search = raw_search[1:]

    parsed_search = parse_qs(search)

    if not ("type" in parsed_search and "variable" in parsed_search):
        raise RuntimeError("Incorrect query parameters provided.")

    variable_type = _ensure_correct_variable_type(parsed_search["type"][0])
    variable_name = parsed_search["variable"][0]
    language: LanguageCode = cast(LanguageCode, parsed_search.get("language", ["en"])[0])

    return variable_name, variable_type, language


@callback(
    Output("control-panel", "children"),
    Output("below-control-and-graph", "children"),
    Input("url", "search"),
)
def handle_group_dropdowns(search: str) -> tuple[list[Any], list[Any]]:

    variable_type: VariableType
    variable_name, variable_type, language = parse_search(search)
    _metadata = _filter_group_metadata(metadata, variable_name, variable_type)

    language_config = get_language_config(language)

    _measure_dropdown = html.Div(id="measure-dropdown")
    if variable_type == "numerical":
        _measure_dropdown = create_measure_dropdown(language)

    first_dropdown = create_grouping_dropdown(
        metadata=_metadata,
        element_id="first-group",
        language=language,
    )
    second_dropdown = create_grouping_dropdown(
        metadata=_metadata,
        element_id="second-group",
        language=language,
    )

    below_control_and_graph_children = [
        dcc.Checklist(
            id="control-panel-checkbox", options=[language_config["hide_control_panel"]]
        ),
        html.Details(
            id="proportional-data-explanation",
            className="removed",
            children=[
                html.Summary(""),
                html.P(
                    id="proportional-data-explanation-content",
                    children=[language_config["proportional_data_explanation"]],
                ),
            ],
            open=True,
        ),
    ]

    children = [
        first_dropdown,
        second_dropdown,
        _measure_dropdown,
        html.Div(
            id="confidence-container",
            children=[
                dcc.Checklist(
                    id="confidence-checkbox",
                    options=[
                        {
                            "label": language_config["confidence_checkbox"],
                            "value": "confidence",
                        },
                    ],
                    value=["confidence"],
                ),
                html.Button(
                    id="confidence-popover-button",
                    className="info-icon",
                    children=[html.I(className="fas fa-info-circle")],
                    style={"padding-left": "0.3em", "font-size": "1.2em"},
                    **{
                        "data-copyright-notice": FONT_AWESOME_COPYRIGHT_NOTICE,
                    },
                ),
                html.Div(
                    id="confidence-popover",
                    className="hidden",
                    children=[language_config["confidence_interval"]],
                ),
            ],
        ),
        dcc.Checklist(
            id="legend-checkbox",
            options=[
                {
                    "label": language_config["show_legend"],
                    "value": "legend",
                },
            ],
            value=["legend"],
        ),
        dcc.Checklist(
            id="bargraph-checkbox",
            className="removed",
            options=[
                {
                    "label": language_config["show_bar_graph"],
                    "value": "bar",
                },
            ],
            value=False,
        ),
        dcc.Checklist(
            id="boxplot-checkbox",
            className="removed",
            options=[
                {
                    "label": language_config["show_boxplot"],
                    "value": "boxplot",
                },
            ],
            value=False,
        ),
        html.Span(
            id="boxplot-flag", key="boxplot-flag", className="removed", children="hide"
        ),
        html.Div(
            id="download-button-container",
            children=[
                html.Button(
                    language_config["download_csv"],
                    id="btn-data-download",
                ),
                dcc.Download(id="data-download", type="str"),
                html.Button(
                    language_config["download_image"],
                    id="btn-image-download",
                ),
                dcc.Download(id="image-download", type="str"),
            ],
            className="download-buttons",
        ),
    ]

    return (children, below_control_and_graph_children)


@callback(
    Output("data-download", "data"),
    dependencies.State("url", "search"),
    dependencies.State("first-group", "value"),
    dependencies.State("second-group", "value"),
    dependencies.State("first-group", "options"),
    Input("btn-data-download", "n_clicks"),
    prevent_initial_call=True,
)
def download(
    search: str,
    first_group_value: str,
    second_group_value: str | None,
    first_group_options: list[PlotlyLabeledOption],
    _: Any,
) -> Any:

    variable_name, variable_type, _ = parse_search(search)
    _data_base_path = get_variable_data_path(variable_type, variable_name)

    grouping, _, second_group_value = handle_grouping(
        first_group_value, second_group_value, first_group_options
    )
    file_name_base = "_".join([variable_name, YEAR, *grouping])
    data_file = _data_base_path.joinpath(file_name_base + ".csv").absolute()
    data = read_csv(data_file)

    # TODO: Refactor Partial redundancy
    _base_path = get_variable_data_path(
        variable_type=variable_type, variable_name=variable_name
    )
    _metadata = []
    if variable_type == "categorical":
        _metadata = [_get_variable_metadata(_base_path)]
    for _variable in grouping:
        _metadata.append(metadata[_variable])

    # TODO: Refactor readability
    with TemporaryDirectory() as tmp_folder:
        path_to_zip = Path(tmp_folder).joinpath("graph")
        mkdir(path_to_zip)
        for _language in ["en", "de"]:
            _data = handle_categorical_labels_and_order(
                data=data, metadata=_metadata, language=_language
            )
            _data.to_csv(
                path_to_zip.joinpath(f"{data_file.stem}_{_language}.csv"), index=False
            )
            with open(
                path_to_zip.joinpath(f"Cite_{_language}.txt"), "w", encoding="utf-8"
            ) as cite_file:
                cite_file.write(citation["base_citation"][_language])
        archive = make_archive(f"{tmp_folder}/{data_file.stem}", "zip", path_to_zip)
        del data
        return dcc.send_file(archive)


@callback(
    Output("image-download", "data"),
    dependencies.State("url", "search"),
    dependencies.State("first-group", "value"),
    dependencies.State("second-group", "value"),
    dependencies.State("first-group", "options"),
    dependencies.State("graph", "figure"),
    Input("btn-image-download", "n_clicks"),
    prevent_initial_call=True,
)
def download_image(
    search: str,
    first_group_value: str,
    second_group_value: str | None,
    first_group_options: list[PlotlyLabeledOption],
    graph: Any,
    _: Any,
) -> Any:

    variable_name, variable_type, language = parse_search(search)

    grouping, _, second_group_value = handle_grouping(
        first_group_value, second_group_value, first_group_options
    )
    file_name_base = "_".join([variable_name, YEAR, *grouping])

    # TODO: Refactor Partial redundancy
    _base_path = get_variable_data_path(
        variable_type=variable_type, variable_name=variable_name
    )

    # TODO: Refactor readability
    with TemporaryDirectory() as tmp_folder:
        path_to_zip = Path(tmp_folder).joinpath("graph")
        mkdir(path_to_zip)
        with open(
            path_to_zip.joinpath(f"Cite_{language}.txt"), "w", encoding="utf-8"
        ) as cite_file:
            cite_file.write(citation["base_citation"][language])
            figure = Figure(**graph)
            figure.update_layout(title=_get_variable_metadata(_base_path)["title"])
        for image_type in ["svg", "png"]:
            figure.write_image(
                file=path_to_zip.joinpath(f"{file_name_base}.{image_type}"),
                format=image_type,
                width=1400,
                height=500,
            )
        archive = make_archive(f"{tmp_folder}/{file_name_base}", "zip", path_to_zip)
        return dcc.send_file(archive)


@callback(
    Output("graph", "figure"),
    Output("second-group", "value"),
    Output("second-group", "options"),
    Output("boxplot-flag", "children"),
    Output("citation-text", "children"),
    Input("first-group", "value"),
    Input("second-group", "value"),
    Input("first-group", "options"),
    Input("confidence-checkbox", "value"),
    Input("legend-checkbox", "value"),
    Input("measure-dropdown", "value"),
    Input("bargraph-checkbox", "value"),
    Input("boxplot-checkbox", "value"),
    dependencies.State("url", "search"),
    dependencies.State("graph", "figure"),
)
def handle_inputs(
    first_group_value: str,
    second_group_value: str | None,
    first_group_options: list[PlotlyLabeledOption],
    show_confidence: str,
    show_legend: str,
    measure: Measure,
    bar_graph: bool,
    boxplot: bool,
    search: str,
    current_graph: Any,
) -> tuple[Figure, str | None, list[PlotlyLabeledOption], str, str]:
    show_boxplot = "show"

    trace_visibility = {}
    if current_graph:
        trace_visibility = {
            trace["name"]: trace.get("visible", True) for trace in current_graph["data"]
        }

    variable_name, variable_type, language = parse_search(search)
    _data_base_path = get_variable_data_path(variable_type, variable_name)

    citation_text = f"Cite as: {citation["base_citation"][language]}"
    if language == "de":
        citation_text = f"Zitiere mit: {citation["base_citation"][language]}"

    grouping, options, second_group_value = handle_grouping(
        first_group_value, second_group_value, first_group_options
    )
    data_file = _data_base_path.joinpath(
        "_".join([variable_name, YEAR, *grouping]) + ".csv"
    ).absolute()
    _dataframe = read_csv(data_file)

    # Language handling and sorting
    _base_path = get_variable_data_path(
        variable_type=variable_type, variable_name=variable_name
    )
    _metadata = []
    if variable_type == "categorical":
        _metadata = [_get_variable_metadata(_base_path)]
    for _variable in grouping:
        _metadata.append(metadata[_variable])
    _dataframe = handle_categorical_labels_and_order(
        data=_dataframe, metadata=_metadata, language=language
    )
    # Language handling and sorting END

    if variable_type == "categorical":
        # It is currently important that variable name is at the end of the grouping list
        # for the grouping of the bar plot to work properly.
        grouping.append(variable_name)
        measure = PROPORTION

    if bar_graph:
        return (
            create_bar_graph_figure(
                _dataframe,
                group=grouping,
                show_legend=bool(show_legend),
                measure=measure,
                language=language,
            ),
            second_group_value,
            options,
            show_boxplot,
            citation_text,
        )
    if _dataframe[measure].max() < BOXPLOT_MIN_VALUE:
        boxplot = False
        show_boxplot = "hide"
    if boxplot:
        return (
            create_numerical_boxplot_figure(
                _dataframe,
                groups=grouping,
                y_title="",
                show_legend=bool(show_legend),
                trace_visibility=trace_visibility,
            ),
            second_group_value,
            options,
            show_boxplot,
            citation_text,
        )

    return (
        create_line_graph_figure(
            _dataframe,
            group=grouping,
            show_confidence=bool(show_confidence),
            show_legend=bool(show_legend),
            measure=measure,
            trace_visibility=trace_visibility,
            language=language,
        ),
        second_group_value,
        options,
        show_boxplot,
        citation_text,
    )


def get_variable_data_path(variable_type: VariableType, variable_name: str) -> Path:

    variable_data_base_path = data_base_path.joinpath(
        f"{variable_type}/{variable_name}/"
    ).resolve()
    # prevent path traversal outside the base path
    if variable_data_base_path.parent.parent != data_base_path:
        raise RuntimeError("Bad variable base path")

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
    app.run(debug=True)
