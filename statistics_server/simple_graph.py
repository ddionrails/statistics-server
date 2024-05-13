"""Builders for numerical and categorical line and bar graphs."""

from collections import deque
from typing import Generator, Iterable

from pandas import DataFrame, Series, read_csv
from pandas.core.groupby.generic import DataFrameGroupBy
from plotly import graph_objects

from statistics_server.layout import (
    PLOT_LANGUAGE_LABELS,
    get_colors_from_palette,
    get_line_types,
    style_numeric_figure,
)
from statistics_server.types import (
    BarPlotGenerator,
    EmptyIterator,
    Measure,
    PlotType,
    ScatterPlotGenerator,
)


def create_traces(
    dataframe: DataFrame,
    group_names: list[str],
    show_confidence: bool = True,
    measure: Measure = "mean",
    plot_type: PlotType = "line",
) -> tuple[ScatterPlotGenerator | BarPlotGenerator, ScatterPlotGenerator | Iterable]:
    groups = dataframe.groupby(group_names)
    if plot_type == "bar":
        main_traces = create_main_trace_bar(groups, measure=measure)
    else:
        main_traces = create_main_trace(groups, measure=measure)
    confidence_traces = EmptyIterator
    if show_confidence:
        confidence_traces = create_confidence_trace_pairs(groups, measure=measure)

    return main_traces, confidence_traces


def numerical_tooltip_formatting(
    n: Series,
    lower_confidence: Series,
    upper_confidence: Series,
    measure: Measure = "mean",
    language: str = "en",
) -> Generator[str, None, None]:
    labels = PLOT_LANGUAGE_LABELS[language]
    for _n, lower, upper in zip(n, lower_confidence, upper_confidence):
        if measure == "proportion":
            yield (
                f"N: {_n}"
                "<br>"
                f"{labels['lower_confidence']}: {lower:.2%}"
                "<br>"
                f"{labels['upper_confidence']}: {upper:.2%}"
            )
            continue

        yield (
            f"N: {_n}"
            "<br>"
            f"{labels['lower_confidence']}: {lower:.2f}"
            "<br>"
            f"{labels['upper_confidence']}: {upper:.2f}"
        )


def create_main_trace_bar(
    groups: DataFrameGroupBy | Iterable, measure: Measure = "proportion"
) -> BarPlotGenerator:
    """Create lines for all groups in a line graph"""
    color_palette = get_colors_from_palette()
    measure_formatter = ": %{y:.2%}<br>%{text}"
    for grouped_by, grouped_data in groups:
        grouping_name = " ".join(grouped_by)
        yield graph_objects.Bar(
            name=grouping_name,
            x=grouped_data["year"],
            y=grouped_data[measure],
            text=list(
                numerical_tooltip_formatting(
                    grouped_data["n"],
                    grouped_data[f"{measure}_lower_confidence"],
                    grouped_data[f"{measure}_upper_confidence"],
                    measure=measure,
                )
            ),
            hovertemplate="Year: %{x}<br>" + measure.capitalize() + measure_formatter,
            textposition="none",
            legendgroup=grouping_name,
        )
    del color_palette


def create_main_trace(
    groups: DataFrameGroupBy | Iterable, measure: Measure = "mean"
) -> ScatterPlotGenerator:
    """Create lines for all groups in a line graph"""
    color_palette = get_colors_from_palette()
    line_types = get_line_types()
    measure_formatter = ": %{y:.2f}<br>%{text}"
    if measure == "proportion":
        measure_formatter = ": %{y:.2%}<br>%{text}"
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
                    measure=measure,
                )
            ),
            mode="lines+markers",
            line={"color": next(color_palette), "dash": next(line_types)},
            marker={"size": 5, "line": {"width": 2}},
            hovertemplate="Year: %{x}<br>" + measure.capitalize() + measure_formatter,
            legendgroup=grouping_name,
        )
    del color_palette


def create_confidence_trace_pairs(
    groups: DataFrameGroupBy | Iterable, measure: Measure = "mean"
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


def create_linegraph_figure(
    dataframe: DataFrame,
    group: list[str] | None = None,
    show_confidence: bool = True,
    measure: Measure = "mean",
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
                dataframe_like_a_groupby, measure=measure
            )

    if group:
        main_traces, confidence_traces = create_traces(
            dataframe, group, show_confidence, measure=measure
        )
    traces = deque(main_traces)
    traces.extend(confidence_traces)

    figure = graph_objects.Figure(list(traces))

    style_numeric_figure(
        figure=figure,
        start_year=dataframe["year"].min(),
        y_max=dataframe[measure].max(),
        plot_type="line",
        measure=measure,
    )

    return figure


def create_bar_graph_figure(
    dataframe: DataFrame,
    group: list[str] | None = None,
    measure: Measure = "mean",
) -> graph_objects.Figure:
    """Assemble figure for a numerical time series statistic"""
    main_traces = EmptyIterator
    confidence_traces = EmptyIterator
    if not group:
        # Make a single DataFrame iterable like a groupby result.
        # (" ") is passed as grouping names instead of ("")
        # because plotly will not group traces otherwise
        dataframe_like_a_groupby = [((" "), dataframe)]
        main_traces = create_main_trace_bar(dataframe_like_a_groupby, measure=measure)

    if group:
        main_traces, confidence_traces = create_traces(
            dataframe, group, show_confidence=False, measure=measure, plot_type="bar"
        )
    traces = deque(main_traces)
    traces.extend(confidence_traces)

    figure = graph_objects.Figure(list(traces))

    style_numeric_figure(
        figure=figure,
        start_year=dataframe["year"].min(),
        y_max=dataframe[measure].max(),
        plot_type="bar",
        measure=measure,
    )

    return figure


if __name__ == "__main__":
    data = read_csv("../tests/test_data/categorical/rentown_year_sampreg.csv")

    _figure = create_bar_graph_figure(data, ["rentown", "sampreg"], measure="proportion")
    _figure.show()

# %%
