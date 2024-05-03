from enum import Enum
from typing import Generator

from plotly.graph_objects import Scatter

type ScatterPlotGenerator = Generator[Scatter, None, None]


class EmptyIterator(Enum):
    """Create an empty iterable for typing."""
