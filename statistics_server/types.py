from enum import Enum
from typing import Generator, Literal

from plotly.graph_objects import Scatter

type ScatterPlotGenerator = Generator[Scatter, None, None]

type CentralMeasure = Literal["mean"] | Literal["median"]


class EmptyIterator(Enum):
    """Create an empty iterable for typing."""


type PlotType = Literal["line"] | Literal["box"]
