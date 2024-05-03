"""Plot generation factories."""

# %% TODO: This is experimental discovery of plotly functions not prod. code

from collections import deque
from typing import Generator, Iterable

from pandas import DataFrame, Series, read_csv
from pandas.core.groupby.generic import DataFrameGroupBy
from plotly import graph_objects

from statistics_server.layout import (PLOT_LANGUAGE_LABELS,
                                      get_colors_from_palette)
from statistics_server.types import ScatterPlotGenerator


def create_traces_for_groups(
    dataframe: DataFrame, group_names: list[str]
) -> tuple[ScatterPlotGenerator, ScatterPlotGenerator]:
    groups = dataframe.groupby(group_names)
    main_traces = create_main_trace(groups)
    confidence_traces = create_confidence_traces(groups)

    return main_traces, confidence_traces


def numerical_tooltip_formatting(
    n: Series, lower_confidence: Series, upper_confidence: Series, language: str = "en"
) -> Generator[str, None, None]:
    labels = PLOT_LANGUAGE_LABELS[language]
    for _n, lower, upper in zip(n, lower_confidence, upper_confidence):
        yield (
            f"N: {_n}"
            "<br>"
            f"{labels['lower_confidence']}: {lower:.2f}"
            "<br>"
            f"{labels['upper_confidence']}: {upper:.2f}"
        )


def create_main_trace(
    groups: DataFrameGroupBy | Iterable,
) -> ScatterPlotGenerator:
    """Create lines for all groups in a line graph"""
    color_palette = get_colors_from_palette()
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


def create_confidence_traces(
    groups: DataFrameGroupBy | Iterable,
) -> ScatterPlotGenerator:
    """Creates a trace for the upper and lower confidence interval bounds."""
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


def style_line_graph_figure(figure: graph_objects.Figure, start_year: int) -> None:
    """Mutate figure to customize styling"""
    figure.update_traces(connectgaps=True)
    figure.update_layout(
        xaxis={"tickmode": "linear", "tick0": start_year, "dtick": 1},
        yaxis={"tickmode": "linear", "tick0": 0, "dtick": 1},
        hoverlabel=dict(font_size=16, font_family="Rockwell"),
    )
    figure.update_yaxes(showline=True, rangemode="tozero", linewidth=1, linecolor="black")
    figure.update_xaxes(showline=True, linewidth=1, linecolor="black")


def create_numerical_figure(
    dataframe: DataFrame, group: list[str] | None = None
) -> graph_objects.Figure:
    """Assemble figure for a numerical time series statistic"""
    main_traces = []
    confidence_traces = []
    if not group:
        # Make a single DataFrame iterable like a groupby result.
        # (" ") is passed as grouping names instead of ("")
        # because plotly will not group traces otherwise
        dataframe_like_a_groupby = [((" "), dataframe)]
        main_traces = create_main_trace(dataframe_like_a_groupby)
        confidence_traces = create_confidence_traces(dataframe_like_a_groupby)

    if group:
        main_traces, confidence_traces = create_traces_for_groups(dataframe, group)
    traces = deque(main_traces)
    traces.extend(confidence_traces)

    figure = graph_objects.Figure(list(traces))

    style_line_graph_figure(figure=figure, start_year=dataframe["year"].min())

    return figure


if __name__ == "__main__":
    data = read_csv("../tests/test_data/numerical/years_injob_year_regtyp_sampreg.csv")

    _figure = create_numerical_figure(data, ["sampreg", "regtyp"])
    _figure.show()

# %%
