from __future__ import annotations

from collections import Counter
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

    gap_threshold = median_delta_ns * 2.5 if median_delta_ns > 0 else min_delta_ns * 2
    gap_indices = np.where(deltas_ns > gap_threshold)[0]
    n_gaps = len(gap_indices)

    gap_details = []
    total_gap_duration_ns = 0

    for idx in gap_indices[:20]:  # Limit to first 20 gaps
        gap_duration_ns = int(deltas_ns[idx])
        expected_samples = (
            int(gap_duration_ns / median_delta_ns) if median_delta_ns > 0 else 1
        )

        gap_info = {
            "gap_index": int(idx),
            "gap_start_time": str(time_array[idx]),
            "gap_end_time": str(time_array[idx + 1]),
            "gap_duration_ns": gap_duration_ns,
            "gap_duration_seconds": gap_duration_ns / 1e9,
            "expected_samples_missing": max(0, expected_samples - 1),
            "gap_ratio": float(gap_duration_ns / median_delta_ns)
            if median_delta_ns > 0
            else 1.0,
        }
        gap_details.append(gap_info)
        total_gap_duration_ns += gap_duration_ns

    total_timespan_ns = int(time_array[-1] - time_array[0])

    sampling_rate_hz = None
    detected_rate_hz = None
    if median_delta_ns > 0:
        raw_rate = 1e9 / median_delta_ns
        sampling_rate_hz = raw_rate

        # Round to common sampling rates
        common_rates = [1, 5, 10, 25, 50, 100, 200, 500, 1000]
        detected_rate_hz = min(common_rates, key=lambda x: abs(x - raw_rate))
        if abs(detected_rate_hz - raw_rate) > raw_rate * 0.2:
            detected_rate_hz = round(raw_rate, 1)

    interval_counts = Counter(deltas_ns)
    most_common_interval = (
        interval_counts.most_common(1)[0] if interval_counts else (0, 0)
    )
    regularity_score = (
        most_common_interval[1] / len(deltas_ns) if len(deltas_ns) > 0 else 0.0
    )

    data_coverage = (
        1.0 - (total_gap_duration_ns / total_timespan_ns)
        if total_timespan_ns > 0
        else 1.0
    )

    result = {
        "min_delta_ns": min_delta_ns,
        "max_delta_ns": max_delta_ns,
        "median_delta_ns": median_delta_ns,
        "n_gaps": n_gaps,
        "total_timespan_ns": total_timespan_ns,
        "sampling_rate_hz": sampling_rate_hz,
        "detected_rate_hz": detected_rate_hz,
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
                "regularity_score": float(regularity_score),
            }
        )

    result.update(
        {
            "gaps": {
                "n_gaps": n_gaps,
                "total_gap_duration_ns": int(total_gap_duration_ns),
                "total_gap_duration_seconds": total_gap_duration_ns / 1e9,
                "data_coverage_ratio": float(data_coverage),
                "gap_details": gap_details,
            },
            "quality": {
                "is_regular": regularity_score > 0.8,
                "has_significant_gaps": n_gaps > 0,
                "jitter_level": "low"
                if delta_cv < 0.1
                else "medium"
                if delta_cv < 0.3
                else "high",
            },
        }
    )

    return result
