from typing import Generator, Iterable, Literal, Self, TypedDict

from pandas import DataFrame
from plotly.graph_objects import Bar, Box, Scatter

type BarPlotGenerator = Generator[Bar, None, None]
type BoxPlotGenerator = Generator[Box, None, None]
type Measure = Literal["mean", "median", "proportion"]
type PlotType = Literal["line", "box", "bar"]
type ScatterPlotGenerator = Generator[Scatter, None, None]
type VariableType = Literal["categorical", "numerical", "numerical"]
type LanguageCode = Literal["en", "de"]


class EmptyIterator:
    """Create an empty iterable for typing."""

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> tuple[tuple[Literal[" "],], DataFrame]:
        raise StopIteration


class EmptyGraphIterator:
    """Create an empty iterable for typing."""

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> Scatter:
        raise StopIteration


type SingleGroupIterator = Iterable[tuple[tuple[Literal[" "],], DataFrame]]


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
