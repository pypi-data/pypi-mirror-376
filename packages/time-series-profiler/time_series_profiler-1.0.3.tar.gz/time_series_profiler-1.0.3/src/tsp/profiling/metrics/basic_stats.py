from __future__ import annotations

from typing import Any

import numpy as np

from ...types import TimeSeriesFrame
from ..registry import register


@register("basic_stats")
def compute_basic_stats(tsf: TimeSeriesFrame) -> dict[str, Any]:
    n_rows = len(tsf.time)
    n_cols = len(tsf.columns)
    is_monotonic = tsf.is_time_monotonic()
    data_array = tsf.to_numpy()
    column_stats = {}

    for i, col_name in enumerate(tsf.columns):
        if data_array.shape[1] > i:
            col_data = data_array[:, i]
            valid_data = col_data[col_data != -1.0]

            if len(valid_data) > 0:
                stats = {
                    "count": len(valid_data),
                    "missing": len(col_data) - len(valid_data),
                    "mean": float(np.mean(valid_data)),
                    "std": float(np.std(valid_data)),
                    "min": float(np.min(valid_data)),
                    "max": float(np.max(valid_data)),
                }

                stats.update(
                    {
                        "median": float(np.median(valid_data)),
                        "q25": float(np.percentile(valid_data, 25)),
                        "q75": float(np.percentile(valid_data, 75)),
                    }
                )
            else:
                stats = {
                    "count": 0,
                    "missing": len(col_data),
                    "mean": None,
                    "std": None,
                    "min": None,
                    "max": None,
                    "median": None,
                    "q25": None,
                    "q75": None,
                }

            dtype_info = tsf.dtypes.get(col_name, "unknown")
            stats["dtype"] = dtype_info

            column_stats[col_name] = stats

    return {
        "n_rows": n_rows,
        "n_cols": n_cols,
        "is_time_monotonic": is_monotonic,
        "columns": column_stats,
    }
