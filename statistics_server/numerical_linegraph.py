"""Line graph generation factories."""

# %% TODO: This is experimental discovery of plotly functions not prod. code

from collections import deque
from typing import Generator, Iterable

from pandas import DataFrame, Series, read_csv
from pandas.core.groupby.generic import DataFrameGroupBy
from plotly import graph_objects

from statistics_server.layout import (PLOT_LANGUAGE_LABELS,
                                      get_colors_from_palette,
                                      style_numeric_figure)
from statistics_server.types import (CentralMeasure, EmptyIterator,
                                     ScatterPlotGenerator)


def create_traces(
    dataframe: DataFrame,
    group_names: list[str],
    show_confidence: bool = True,
    measure: CentralMeasure = "mean",
) -> tuple[ScatterPlotGenerator, ScatterPlotGenerator | Iterable]:
    groups = dataframe.groupby(group_names)
    main_traces = create_main_trace(groups, measure=measure)
    confidence_traces = EmptyIterator
    if show_confidence:
        confidence_traces = create_confidence_trace_pairs(groups, measure=measure)

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
    groups: DataFrameGroupBy | Iterable, measure: CentralMeasure = "mean"
) -> ScatterPlotGenerator:
    """Create lines for all groups in a line graph"""
    color_palette = get_colors_from_palette()
    for grouped_by, grouped_data in groups:
        grouping_name = " ".join(grouped_by)
        yield graph_objects.Scatter(
            name=grouping_name,
            x=grouped_data["year"],
            y=grouped_data[measure],
            text=list(
                numerical_tooltip_formatting(
                    grouped_data["n"],
                    grouped_data[f"{measure}_lower_confidence"],
                    grouped_data[f"{measure}_upper_confidence"],
                )
            ),
            mode="lines+markers",
            line={"color": next(color_palette)},
            marker={"size": 5, "line": {"width": 2}},
            hovertemplate="Year: %{x}<br>"
            + measure.capitalize()
            + ": %{y:.2f}<br>%{text}",
            legendgroup=grouping_name,
        )
    del color_palette


def create_confidence_trace_pairs(
    groups: DataFrameGroupBy | Iterable, measure: CentralMeasure = "mean"
) -> ScatterPlotGenerator:
    """Creates a trace for the upper and lower confidence interval bounds."""
    for grouped_by, grouped_data in groups:
        grouping_name = " ".join(grouped_by)

        yield graph_objects.Scatter(
            name=grouping_name,
            x=grouped_data["year"],
            y=grouped_data[f"{measure}_upper_confidence"],
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
            y=grouped_data[f"{measure}_lower_confidence"],
            marker={"color": "#444"},
            line={"width": 0},
            mode="lines",
            fillcolor="rgba(68, 68, 68, 0.15)",
            fill="tonexty",
            showlegend=False,
            hoverinfo="skip",
            legendgroup=grouping_name,
        )


def create_numerical_linegraph_figure(
    dataframe: DataFrame,
    group: list[str] | None = None,
    show_confidence: bool = True,
    central_measure: CentralMeasure = "mean",
) -> graph_objects.Figure:
    """Assemble figure for a numerical time series statistic"""
    main_traces = EmptyIterator
    confidence_traces = EmptyIterator
    if not group:
        # Make a single DataFrame iterable like a groupby result.
        # (" ") is passed as grouping names instead of ("")
        # because plotly will not group traces otherwise
        dataframe_like_a_groupby = [((" "), dataframe)]
        main_traces = create_main_trace(dataframe_like_a_groupby)
        if show_confidence:
            confidence_traces = create_confidence_trace_pairs(
                dataframe_like_a_groupby, measure=central_measure
            )

    if group:
        main_traces, confidence_traces = create_traces(
            dataframe, group, show_confidence, measure=central_measure
        )
    traces = deque(main_traces)
    traces.extend(confidence_traces)

    figure = graph_objects.Figure(list(traces))

    style_numeric_figure(
        figure=figure,
        start_year=dataframe["year"].min(),
        y_max=dataframe[central_measure].max(),
        plot_type="line",
    )

    return figure


if __name__ == "__main__":
    data = read_csv("../tests/test_data/numerical/years_injob_year_regtyp_sampreg.csv")

    _figure = create_numerical_linegraph_figure(
        data, ["sampreg", "regtyp"], central_measure="median"
    )
    _figure.show()

# %%
