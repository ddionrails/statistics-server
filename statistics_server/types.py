from enum import Enum
from typing import Generator, Literal, TypedDict

from plotly.graph_objects import Bar, Scatter

type BarPlotGenerator = Generator[Bar, None, None]
type Measure = Literal["mean", "median", "proportion"]
type PlotType = Literal["line", "box", "bar"]
type ScatterPlotGenerator = Generator[Scatter, None, None]
type VariableType = Literal["categorical", "numerical", "numerical"]
type LanguageCode = Literal["en", "de"]


class EmptyIterator(Enum):
    """Create an empty iterable for typing."""


class PlotlyLabeledOption(TypedDict):
    """Single entry of a plotly dropdown."""

    value: str | None
    label: str


class VariableMetadata(TypedDict):

    label: str
    label_de: str
    variable: str
    values: list[int]
    value_labels: list[str]
    value_labels_de: list[str]
    groups: list[str]


class GroupingMetadata(TypedDict):
    label: str
    value: str | None


class MeasureMetadata(TypedDict):
    mean: str
    median: str


class UnselectedGroup(TypedDict):
    en: GroupingMetadata
    de: GroupingMetadata


class MeasureNames(TypedDict):
    en: MeasureMetadata
    de: MeasureMetadata


class UITranslation(TypedDict):
    unselected_group: UnselectedGroup
    measure_names: MeasureNames
