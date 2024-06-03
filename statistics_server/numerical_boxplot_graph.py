"""Boxplot generation factories."""

# %%
from collections import deque
from typing import Generator, Iterable

from pandas import read_csv
from pandas.core.groupby.generic import DataFrameGroupBy
from plotly import graph_objects

from statistics_server.layout import get_colors_from_palette, style_numeric_figure
from statistics_server.types import EmptyIterator
from statistics_server.simple_graph import visibility_handler


def create_boxplot_traces(
    groups: DataFrameGroupBy | Iterable, trace_visibility
) -> Generator[graph_objects.Box, None, None]:
    color_palette = get_colors_from_palette()
    _visibility_handler = visibility_handler(trace_visibility)
    for grouped_by, grouped_data in groups:
        group_key = " ".join(grouped_by)

        next(_visibility_handler)
        visible = _visibility_handler.send(group_key)

        yield graph_objects.Box(
            x=grouped_data["year"],
            q1=grouped_data["lower_quartile"],
            median=grouped_data["boxplot_median"],
            q3=grouped_data["upper_quartile"],
            lowerfence=grouped_data["lower_whisker"],
            upperfence=grouped_data["upper_whisker"],
            name=" ".join(grouped_by),
            marker_color=next(color_palette),
            visible=visible,
        )


def create_numerical_boxplot_figure(
    dataframe,
    groups: list[str],
    y_title: str = "",
    show_legend: bool = True,
    trace_visibility={},
):

    start_year = dataframe["year"].min()

    traces = EmptyIterator
    if groups:
        traces = create_boxplot_traces(dataframe.groupby(groups), trace_visibility)
    if not groups:
        traces = create_boxplot_traces([((" "), dataframe)], trace_visibility)

    figure = graph_objects.Figure(list(deque(traces)))

    style_numeric_figure(
        figure, start_year, dataframe["upper_whisker"].max(), plot_type="box"
    )

    figure.update_layout(
        yaxis_title=y_title,
        boxmode="group",  # group together boxes of the different traces for each value of x
        showlegend=show_legend,
    )

    return figure


if __name__ == "__main__":
    data = read_csv("../tests/test_data/numerical/years_injob_year_regtyp_sampreg.csv")

    _figure = create_numerical_boxplot_figure(
        data, ["regtyp", "sampreg"], "Years spend in Job"
    )
    _figure.show()

# %%
