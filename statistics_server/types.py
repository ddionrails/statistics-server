from typing import Generator

from plotly.graph_objects import Scatter

type ScatterPlotGenerator = Generator[Scatter, None, None]
