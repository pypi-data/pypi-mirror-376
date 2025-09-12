from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime
from typing import Any, Protocol

import numpy as np


class TimeSeriesFrame(Protocol):
    @property
    def time(self) -> Sequence[datetime]:
        ...

    @property
    def columns(self) -> Sequence[str]:
        ...

    @property
    def dtypes(self) -> Mapping[str, str]:
        ...

    @property
    def entity_cols(self) -> tuple[str, ...]:
        ...

    def select_columns(self, cols: Sequence[str]) -> TimeSeriesFrame:
        ...

    def to_numpy(self) -> np.ndarray:
        ...

    def is_time_monotonic(self) -> bool:
        ...

    def has_entities(self) -> bool:
        ...

    def iter_groups(self) -> Iterator[tuple[tuple[Any, ...], TimeSeriesFrame]]:
        ...
