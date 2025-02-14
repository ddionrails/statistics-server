"""Builders for numerical and categorical line and bar graphs."""

# TODO: Refactor types
# TODO: Change plot creation in a way that it only renders from first to last value
# not from 1982 - 2023

# %%

from collections import deque
from typing import Generator, Literal

from pandas import DataFrame, Series, read_csv
from pandas.core.groupby.generic import DataFrameGroupBy
from plotly import graph_objects

from statistics_server.language_handling import MEASURE_TRANSLATION, YEAR_TRANSLATION
from statistics_server.layout import (
    PLOT_LANGUAGE_LABELS,
    get_colors_from_palette,
    get_line_types,
    style_numeric_figure,
)
from statistics_server.types import (
    BarPlotGenerator,
    EmptyGraphIterator,
    EmptyIterator,
    Measure,
    PlotType,
    ScatterPlotGenerator,
    SingleGroupIterator,
)

DEFAULT_MAX_VISIBLE_TRACES = 4


def visibility_handler(
    trace_visibility: dict[str, str | bool]
) -> Generator[str | bool | None, str, None]:
    """Manage visible traces

    Make all but the first x traces invisible except when
    visibility changes were made manually.
    """
    visible: str | bool = True
    for _ in range(0, DEFAULT_MAX_VISIBLE_TRACES):
        group_key = yield  # type: ignore

        visible = True
        if group_key in trace_visibility:
            visible = trace_visibility[group_key]
        yield visible

    while True:
        visible = "legendonly"
        group_key = yield  # type: ignore
        if group_key in trace_visibility:
            visible = trace_visibility[group_key]
        yield visible


def create_traces(
    dataframe: DataFrame,
    group_names: list[str],
    show_confidence: bool = True,
    measure: Measure = "mean",
    plot_type: PlotType = "line",
    trace_visibility: dict[str, str | bool] = {},
    language: Literal["en"] | Literal["de"] = "en",
) -> tuple[
    ScatterPlotGenerator | BarPlotGenerator, ScatterPlotGenerator | EmptyGraphIterator
]:
    groups = dataframe.groupby(group_names)
    main_traces: ScatterPlotGenerator | BarPlotGenerator

    if plot_type == "bar":
        main_traces = create_main_trace_bar(groups, measure=measure, language=language)
    else:
        main_traces = create_main_trace(
            groups,
            measure=measure,
            trace_visibility=trace_visibility,
            language=language,
        )
    confidence_traces: ScatterPlotGenerator | EmptyGraphIterator = EmptyGraphIterator()
    if show_confidence:
        confidence_traces = create_confidence_trace_pairs(
            groups, measure=measure, trace_visibility=trace_visibility
        )

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
    groups: DataFrameGroupBy | SingleGroupIterator,
    measure: Measure = "proportion",
    trace_visibility: dict["str", "str"] = {},
    language: Literal["en"] | Literal["de"] = "en",
) -> BarPlotGenerator:
    """Create lines for all groups in a line graph"""
    color_palette = get_colors_from_palette()
    measure_formatter = ": %{y:.2%}<br>%{text}"

    group_color_map = {}

    for grouped_by, grouped_data in groups:
        show_legend = False
        if grouped_by[-1] not in group_color_map:
            group_color_map[grouped_by[-1]] = next(color_palette)
            show_legend = True

        yield graph_objects.Bar(
            name=grouped_by[-1],
            x=[
                grouped_data["year"],
                [grouped_by[:-1]] * len(grouped_data["year"]),
            ],
            y=grouped_data[measure],
            text=list(
                numerical_tooltip_formatting(
                    grouped_data["n"],
                    grouped_data[f"{measure}_lower_confidence"],
                    grouped_data[f"{measure}_upper_confidence"],
                    measure=measure,
                    language=language,
                )
            ),
            hovertemplate=YEAR_TRANSLATION[language]
            + ": %{x}<br>"
            + MEASURE_TRANSLATION[language][measure.lower()]
            + measure_formatter,
            textposition="none",
            marker_color=group_color_map[grouped_by[-1]],
            legendgroup=grouped_by[-1],
            showlegend=show_legend,
        )
    del color_palette


def create_main_trace(
    groups: DataFrameGroupBy | SingleGroupIterator,
    measure: Measure = "mean",
    trace_visibility: dict[str, str | bool] = {},
    language: Literal["en"] | Literal["de"] = "en",
) -> ScatterPlotGenerator:
    """Create lines for all groups in a line graph"""
    color_palette = get_colors_from_palette()
    line_types = get_line_types()
    measure_formatter = ": %{y:.2f}<br>%{text}"
    if measure == "proportion":
        measure_formatter = ": %{y:.2%}<br>%{text}"

    _visibility_handler = visibility_handler(trace_visibility)

    for grouped_by, grouped_data in groups:
        group_key = " ".join(grouped_by)
        next(_visibility_handler)
        visible = _visibility_handler.send(group_key)

        yield graph_objects.Scatter(
            name=group_key,
            x=grouped_data["year"],
            y=grouped_data[measure],
            text=list(
                numerical_tooltip_formatting(
                    grouped_data["n"],
                    grouped_data[f"{measure}_lower_confidence"],
                    grouped_data[f"{measure}_upper_confidence"],
                    measure=measure,
                    language=language,
                )
            ),
            mode="lines+markers",
            line={"color": next(color_palette), "dash": next(line_types)},
            marker={"size": 5, "line": {"width": 2}},
            hovertemplate=YEAR_TRANSLATION[language]
            + ": %{x}<br>"
            + MEASURE_TRANSLATION[language][measure.lower()]
            + measure_formatter,
            legendgroup=group_key,
            visible=visible,
        )
    del _visibility_handler
    del color_palette


def create_confidence_trace_pairs(
    groups: DataFrameGroupBy | EmptyIterator | SingleGroupIterator,
    measure: Measure = "mean",
    trace_visibility: dict[str, str | bool] = {},
) -> ScatterPlotGenerator:
    """Creates a trace for the upper and lower confidence interval bounds."""
    _visibility_handler = visibility_handler(trace_visibility)
    for grouped_by, grouped_data in groups:  # type: ignore[union-attr]
        group_key = " ".join(grouped_by)
        next(_visibility_handler)
        visible = _visibility_handler.send(group_key)

        yield graph_objects.Scatter(
            name=group_key,
            x=grouped_data["year"],
            y=grouped_data[f"{measure}_upper_confidence"],
            mode="lines",
            marker={"color": "#444"},
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
            legendgroup=group_key,
            visible=visible,
        )

        yield graph_objects.Scatter(
            name=group_key,
            x=grouped_data["year"],
            y=grouped_data[f"{measure}_lower_confidence"],
            marker={"color": "#444"},
            line={"width": 0},
            mode="lines",
            fillcolor="rgba(68, 68, 68, 0.15)",
            fill="tonexty",
            showlegend=False,
            hoverinfo="skip",
            legendgroup=group_key,
            visible=visible,
        )
    del _visibility_handler


def create_line_graph_figure(
    dataframe: DataFrame,
    group: list[str] | None = None,
    show_confidence: bool = True,
    show_legend: bool = True,
    measure: Measure = "mean",
    trace_visibility: dict[str, str | bool] = {},
    language: Literal["en"] | Literal["de"] = "en",
) -> graph_objects.Figure:
    """Assemble figure for a numerical time series statistic"""
    main_traces: EmptyIterator | ScatterPlotGenerator | BarPlotGenerator = EmptyIterator()
    confidence_traces: EmptyGraphIterator | ScatterPlotGenerator = EmptyGraphIterator()
    if not group:
        # Make a single DataFrame iterable like a groupby result.
        # (" ") is passed as grouping names instead of ("")
        # because plotly will not group traces otherwise
        dataframe_like_a_groupby: SingleGroupIterator = [((" ",), dataframe)]
        main_traces = create_main_trace(
            dataframe_like_a_groupby,
            measure=measure,
            trace_visibility=trace_visibility,
            language=language,
        )
        if show_confidence:
            confidence_traces = create_confidence_trace_pairs(
                dataframe_like_a_groupby,
                measure=measure,
                trace_visibility=trace_visibility,
            )

    if group:
        main_traces, confidence_traces = create_traces(
            dataframe,
            group,
            show_confidence,
            measure=measure,
            trace_visibility=trace_visibility,
            language=language,
        )
    traces = deque(main_traces)
    traces.extend(confidence_traces)

    figure = graph_objects.Figure(list(traces))
    if not show_legend:
        figure.update_layout(showlegend=False)

    style_numeric_figure(
        figure=figure,
        start_year=dataframe[~dataframe[measure].isna()]["year"].min(),
        end_year=dataframe[~dataframe[measure].isna()]["year"].max(),
        y_max=dataframe[measure].max(),
        plot_type="line",
        measure=measure,
    )

    return figure


def create_bar_graph_figure(
    dataframe: DataFrame,
    group: list[str] | None = None,
    show_legend: bool = True,
    measure: Measure = "mean",
    language: Literal["en"] | Literal["de"] = "en",
) -> graph_objects.Figure:
    """Assemble figure for a numerical time series statistic"""
    main_traces: BarPlotGenerator | ScatterPlotGenerator
    confidence_traces: EmptyGraphIterator | ScatterPlotGenerator = EmptyGraphIterator()
    if not group:
        # Make a single DataFrame iterable like a groupby result.
        # (" ") is passed as grouping names instead of ("")
        # because plotly will not group traces otherwise
        dataframe_like_a_groupby: SingleGroupIterator = [((" ",), dataframe)]
        main_traces = create_main_trace_bar(
            dataframe_like_a_groupby, measure=measure, language=language
        )

    if group:
        main_traces, confidence_traces = create_traces(
            dataframe, group, show_confidence=False, measure=measure, plot_type="bar"
        )
    traces = deque(main_traces)
    traces.extend(confidence_traces)

    figure = graph_objects.Figure(list(traces))

    figure.update_layout(showlegend=False)

    style_numeric_figure(
        figure=figure,
        start_year=dataframe["year"].min(),
        end_year=dataframe["year"].max(),
        y_max=dataframe[measure].max(),
        plot_type="bar",
        measure=measure,
    )
    # figure.update_layout(xaxis={"showticklabels": False})
    # figure.update_layout(show_legend={"showticklabels": False})

    return figure


if __name__ == "__main__":
    data = read_csv("../tests/test_data/numerical/years_injob/years_injob_year.csv")

    _figure = create_line_graph_figure(data, measure="median")
    _figure.show()

# %%
