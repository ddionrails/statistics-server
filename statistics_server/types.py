from enum import Enum
from typing import Generator, Literal

from plotly.graph_objects import Bar, Scatter

type ScatterPlotGenerator = Generator[Scatter, None, None]
type BarPlotGenerator = Generator[Bar, None, None]

type Measure = Literal["mean"] | Literal["median"] | Literal["proportion"]


class EmptyIterator(Enum):
    """Create an empty iterable for typing."""


type PlotType = Literal["line"] | Literal["box"] | Literal["bar"]
