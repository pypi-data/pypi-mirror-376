from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd


class PandasTS:
    def __init__(
        self,
        df: pd.DataFrame,
        time_col: str | None = None,
        entity_cols: Sequence[str] = (),
    ):
        self.df = df.copy()
        self._time_col = time_col
        self._entity_cols = tuple(entity_cols)

        if time_col is None:
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValueError(
                    "If time_col is None, DataFrame must have DatetimeIndex"
                )
            self._time_values = df.index.to_pydatetime()
        else:
            if time_col not in df.columns:
                raise ValueError(f"Time column '{time_col}' not found in DataFrame")
            time_series = pd.to_datetime(df[time_col])
            self._time_values = [dt.to_pydatetime() for dt in time_series]

        for col in entity_cols:
            if col not in df.columns:
                raise ValueError(f"Entity column '{col}' not found in DataFrame")

        excluded_cols = set(entity_cols)
        if time_col is not None:
            excluded_cols.add(time_col)
        self._data_columns = [col for col in df.columns if col not in excluded_cols]

    @property
    def time(self) -> Sequence[datetime]:
        return self._time_values

    @property
    def columns(self) -> Sequence[str]:
        return self._data_columns

    @property
    def dtypes(self) -> Mapping[str, str]:
        return {col: str(self.df[col].dtype) for col in self._data_columns}

    @property
    def entity_cols(self) -> tuple[str, ...]:
        return self._entity_cols

    def select_columns(self, cols: Sequence[str]) -> PandasTS:
        missing_cols = set(cols) - set(self._data_columns)
        if missing_cols:
            raise ValueError(f"Columns not found: {missing_cols}")

        keep_cols = list(cols)
        if self._time_col is not None:
            keep_cols.append(self._time_col)
        keep_cols.extend(self._entity_cols)

        new_df = self.df[keep_cols]
        return PandasTS(new_df, self._time_col, self._entity_cols)

    def to_numpy(self) -> np.ndarray:
        if not self._data_columns:
            return np.empty((len(self.df), 0))

        data_df = self.df[self._data_columns]
        result_arrays = []

        for col in self._data_columns:
            series = data_df[col]

            if pd.api.types.is_numeric_dtype(series):
                arr = series.astype(float).fillna(-1.0).values
            else:
                if pd.api.types.is_categorical_dtype(series):
                    codes = series.cat.codes.values
                else:
                    cat_series = pd.Categorical(series)
                    codes = cat_series.codes

                arr = codes.astype(float)

            result_arrays.append(arr)

        return np.column_stack(result_arrays)

    def is_time_monotonic(self) -> bool:
        if len(self._time_values) <= 1:
            return True

        time_array = np.array(self._time_values, dtype="datetime64[ns]")
        return np.all(time_array[1:] >= time_array[:-1])

    def has_entities(self) -> bool:
        return len(self._entity_cols) > 0

    def iter_groups(self) -> Iterator[tuple[tuple[Any, ...], PandasTS]]:
        if not self.has_entities():
            yield ((), self)
            return

        grouped = self.df.groupby(list(self._entity_cols))

        for group_key, group_df in grouped:
            if not isinstance(group_key, tuple):
                group_key = (group_key,)

            group_ts = PandasTS(group_df, self._time_col, self._entity_cols)
            yield (group_key, group_ts)


def wrap(
    df: pd.DataFrame, time_col: str | None = None, entity_cols: Sequence[str] = ()
) -> PandasTS:
    return PandasTS(df, time_col, entity_cols)
