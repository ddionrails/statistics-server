"""Plot generation factories."""

# %% TODO: This is experimental discovery of plotly functions not prod. code

from collections import deque
from typing import Iterable

from pandas import DataFrame, Series, read_csv
from pandas.core.groupby.generic import DataFrameGroupBy
from plotly import graph_objects

COLORS = [
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
]

LANGUAGE_LABELS = {
    "en": {
        "lower_confidence": "Lower confidence",
        "upper_confidence": "Upper confidence",
    },
    "de": {
        "lower_confidence": "Untere Konfidenz Grenze",
        "upper_confidence": "Obere Konfidenz Grenze",
    },
}


def get_color():
    while True:
        for color in COLORS:
            yield color


def create_layers_for_groups(dataframe: DataFrame, group_names):
    groups = dataframe.groupby(group_names)
    main_layers = []
    confidence_layers = []
    main_layers = create_main_layer(groups)
    confidence_layers = create_confidence_layers(groups)

    return main_layers, confidence_layers


def numerical_tooltip_formatting(
    n: Series, lower_confidence: Series, upper_confidence: Series, language: str = "en"
):
    labels = LANGUAGE_LABELS[language]
    for _n, lower, upper in zip(n, lower_confidence, upper_confidence):
        yield (
            f"N: {_n}"
            "<br>"
            f"{labels['lower_confidence']}: {lower:.2f}"
            "<br>"
            f"{labels['upper_confidence']}: {upper:.2f}"
        )


def create_main_layer(groups: DataFrameGroupBy | Iterable):
    color_palette = get_color()
    for grouped_by, grouped_data in groups:
        grouping_name = " ".join(grouped_by)
        yield graph_objects.Scatter(
            name=grouping_name,
            x=grouped_data["year"],
            y=grouped_data["mean"],
            text=list(
                numerical_tooltip_formatting(
                    grouped_data["n"],
                    grouped_data["mean_lower_confidence"],
                    grouped_data["mean_upper_confidence"],
                )
            ),
            mode="lines+markers",
            line={"color": next(color_palette)},
            marker={"size": 5, "line": {"width": 2}},
            hovertemplate="Year: %{x}<br>Mean: %{y:.2f}<br>%{text}",
            legendgroup=grouping_name,
        )
    del color_palette


def create_confidence_layers(groups):
    for grouped_by, grouped_data in groups:
        grouping_name = " ".join(grouped_by)

        yield graph_objects.Scatter(
            name=grouping_name,
            x=grouped_data["year"],
            y=grouped_data["mean_upper_confidence"],
            mode="lines",
            marker={"color": "#444"},
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
            legendgroup=grouping_name,
        )

        yield graph_objects.Scatter(
            name=grouping_name,
            x=grouped_data["year"],
            y=grouped_data["mean_lower_confidence"],
            marker={"color": "#444"},
            line={"width": 0},
            mode="lines",
            fillcolor="rgba(68, 68, 68, 0.15)",
            fill="tonexty",
            showlegend=False,
            hoverinfo="skip",
            legendgroup=grouping_name,
        )


def create_numerical_plot(dataframe, group: str = ""):
    main_layers = []
    confidence_layers = []
    if not group:
        # Make a single DataFrame iterable like a groupby result.
        # " " is passed instead of "" because plotly will not group traces otherwise
        dataframe_like_a_groupby = [((" "), dataframe)]
        main_layers = create_main_layer(dataframe_like_a_groupby)
        confidence_layers = create_confidence_layers(dataframe_like_a_groupby)

    if group:
        main_layers, confidence_layers = create_layers_for_groups(dataframe, group)
    layers = deque(main_layers)
    layers.extend(confidence_layers)

    figure = graph_objects.Figure(list(layers))

    figure.update_traces(connectgaps=True)
    figure.update_layout(
        xaxis={"tickmode": "linear", "tick0": dataframe["year"].min(), "dtick": 1},
        yaxis={"tickmode": "linear", "tick0": 0, "dtick": 1},
        hoverlabel=dict(font_size=16, font_family="Rockwell"),
    )
    figure.update_yaxes(showline=True, rangemode="tozero", linewidth=1, linecolor="black")
    figure.update_xaxes(showline=True, linewidth=1, linecolor="black")

    return figure


if __name__ == "__main__":
    data = read_csv("../tests/test_data/numerical/years_injob_year_regtyp_sampreg.csv")

    _figure = create_numerical_plot(data, ["sampreg", "regtyp"])
    _figure.show()

# %%
