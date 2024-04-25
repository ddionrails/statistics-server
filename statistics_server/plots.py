"""Plot generation factories."""

# %% TODO: This is experimental discovery of plotly functions not prod. code

from plotly import graph_objects
from pandas import read_csv

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


def get_color():
    while True:
        for color in COLORS:
            yield color


def create_numerical_plot(dataframe, group: str = ""):
    main_layers = []
    confidence_layers = []
    color_palette = get_color()
    if group:
        group_values = dataframe[group].unique()
    if not group:
        main_layers = [
            graph_objects.Scatter(
                name="Measurement",
                x=dataframe["year"],
                y=dataframe["mean"],
                mode="lines+markers",
                line={"color": "rgb(31, 119, 180)"},
                marker={"size": 5, "line": {"width": 2}},
            )
        ]
        confidence_layers = [
            graph_objects.Scatter(
                name="Upper Bound",
                x=dataframe["year"],
                y=dataframe["mean_upper_confidence"],
                mode="lines",
                marker={"color": "#444"},
                line={"width": 0},
                showlegend=False,
            ),
            graph_objects.Scatter(
                name="Lower Bound",
                x=dataframe["year"],
                y=dataframe["mean_lower_confidence"],
                marker={"color": "#444"},
                line={"width": 0},
                mode="lines",
                fillcolor="rgba(68, 68, 68, 0.3)",
                fill="tonexty",
                showlegend=False,
            ),
        ]
    if group:
        for group_value in group_values:
            group_data = dataframe[dataframe[group] == group_value]

            main_layers.append(
                graph_objects.Scatter(
                    name=f"{group_value}",
                    x=group_data["year"],
                    y=group_data["mean"],
                    mode="lines+markers",
                    line={"color": next(color_palette)},
                    marker={"size": 5, "line": {"width": 2}},
                )
            )

            confidence_layers.append(
                graph_objects.Scatter(
                    name=f"{group_value} Upper Bound",
                    x=group_data["year"],
                    y=group_data["mean_upper_confidence"],
                    mode="lines",
                    marker={"color": "#444"},
                    line={"width": 0},
                    showlegend=False,
                )
            )
            confidence_layers.append(
                graph_objects.Scatter(
                    name=f"{group_value} Lower Bound",
                    x=group_data["year"],
                    y=group_data["mean_lower_confidence"],
                    marker={"color": "#444"},
                    line={"width": 0},
                    mode="lines",
                    fillcolor="rgba(68, 68, 68, 0.3)",
                    fill="tonexty",
                    showlegend=False,
                ),
            )

    figure = graph_objects.Figure([*main_layers, *confidence_layers])

    figure.update_traces(connectgaps=True)
    figure.update_layout(
        xaxis={"tickmode": "linear", "tick0": dataframe["year"].min(), "dtick": 1},
        yaxis={"tickmode": "linear", "tick0": 0, "dtick": 1},
    )
    figure.update_yaxes(showline=True, rangemode="tozero", linewidth=1, linecolor="black")
    figure.update_xaxes(showline=True, linewidth=1, linecolor="black")

    del color_palette
    return figure


if __name__ == "__main__":
    data = read_csv("../tests/test_data/numerical/years_injob_year_sampreg.csv")

    _figure = create_numerical_plot(data, "sampreg")
    _figure.show()
