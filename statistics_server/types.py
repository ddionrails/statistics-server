from enum import Enum
from typing import Generator, Literal, TypedDict

from plotly.graph_objects import Bar, Scatter

type BarPlotGenerator = Generator[Bar, None, None]
type Measure = Literal["mean", "median", "proportion"]
type PlotType = Literal["line", "box", "bar"]
type ScatterPlotGenerator = Generator[Scatter, None, None]
type VariableType = Literal["categorical", "numerical", "numerical"]


class EmptyIterator(Enum):
    """Create an empty iterable for typing."""


class PlotlyLabeledOption(TypedDict):
    value: str | None
    label: str
