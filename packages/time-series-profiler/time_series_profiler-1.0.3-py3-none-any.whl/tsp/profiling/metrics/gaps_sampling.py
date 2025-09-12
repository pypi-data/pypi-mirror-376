from __future__ import annotations

from typing import Any

import numpy as np

from ...types import TimeSeriesFrame
from ..registry import register


@register("gaps_sampling")
def compute_gaps_sampling(tsf: TimeSeriesFrame) -> dict[str, Any]:
    time_values = tsf.time

    if len(time_values) <= 1:
        return {
            "min_delta_ns": None,
            "max_delta_ns": None,
            "median_delta_ns": None,
            "n_gaps": 0,
            "total_timespan_ns": 0,
            "sampling_rate_hz": None,
        }

    time_array = np.array(time_values, dtype="datetime64[ns]")
    deltas_ns = np.diff(time_array).astype("int64")

    min_delta_ns = int(np.min(deltas_ns))
    max_delta_ns = int(np.max(deltas_ns))
    median_delta_ns = int(np.median(deltas_ns))

    if min_delta_ns > 0:
        gap_threshold = min_delta_ns * 1.5
        n_gaps = int(np.sum(deltas_ns > gap_threshold))
    else:
        n_gaps = 0

    total_timespan_ns = int(time_array[-1] - time_array[0])

    sampling_rate_hz = None
    if median_delta_ns > 0:
        sampling_rate_hz = 1e9 / median_delta_ns

    result = {
        "min_delta_ns": min_delta_ns,
        "max_delta_ns": max_delta_ns,
        "median_delta_ns": median_delta_ns,
        "n_gaps": n_gaps,
        "total_timespan_ns": total_timespan_ns,
        "sampling_rate_hz": sampling_rate_hz,
    }

    result.update(
        {
            "min_delta_seconds": min_delta_ns / 1e9,
            "max_delta_seconds": max_delta_ns / 1e9,
            "median_delta_seconds": median_delta_ns / 1e9,
            "total_timespan_seconds": total_timespan_ns / 1e9,
        }
    )

    if len(deltas_ns) > 0:
        delta_std = np.std(deltas_ns)
        delta_cv = (
            delta_std / np.mean(deltas_ns) if np.mean(deltas_ns) > 0 else float("inf")
        )

        result.update(
            {
                "delta_std_ns": int(delta_std),
                "delta_coefficient_of_variation": float(delta_cv),
                "is_regular_sampling": delta_cv < 0.1,
            }
        )

    return result
