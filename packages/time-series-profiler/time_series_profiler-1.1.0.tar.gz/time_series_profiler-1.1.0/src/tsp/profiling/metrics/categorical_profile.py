from __future__ import annotations

from typing import Any

import numpy as np

from ...types import TimeSeriesFrame
from ..registry import register


def _compute_entropy(counts: np.ndarray) -> float:
    if len(counts) == 0:
        return 0.0

    probs = counts / np.sum(counts)
    probs = probs[probs > 0]

    if len(probs) <= 1:
        return 0.0

    return float(-np.sum(probs * np.log2(probs)))


@register("categorical_profile")
def compute_categorical_profile(tsf: TimeSeriesFrame) -> dict[str, Any]:
    dtypes = tsf.dtypes

    categorical_cols = [
        col
        for col, dtype in dtypes.items()
        if "object" in dtype.lower()
        or "category" in dtype.lower()
        or "string" in dtype.lower()
    ]

    if not categorical_cols:
        return {"message": "No categorical columns found"}

    results = {}
    pandas_df = getattr(tsf, "df", None)

    for col in categorical_cols:
        col_result = {}

        if pandas_df is not None and col in pandas_df.columns:
            series = pandas_df[col]
            value_counts = series.value_counts(dropna=False)

            col_result["cardinality"] = len(value_counts)
            col_result["total_count"] = len(series)
            col_result["missing_count"] = int(series.isna().sum())
            col_result["non_missing_count"] = (
                col_result["total_count"] - col_result["missing_count"]
            )

            top_10 = value_counts.head(10)
            col_result["top_counts"] = [
                {"value": str(value), "count": int(count)}
                for value, count in top_10.items()
            ]

            if col_result["non_missing_count"] > 0:
                non_missing_counts = value_counts.dropna().values
                col_result["entropy"] = _compute_entropy(non_missing_counts)
            else:
                col_result["entropy"] = 0.0

            if col_result["non_missing_count"] > 0:
                most_common_value = value_counts.index[0]
                most_common_count = value_counts.iloc[0]
                col_result["most_common"] = {
                    "value": str(most_common_value),
                    "count": int(most_common_count),
                    "frequency": float(
                        most_common_count / col_result["non_missing_count"]
                    ),
                }

                expected_uniform_count = (
                    col_result["non_missing_count"] / col_result["cardinality"]
                )
                uniformity = (
                    1.0 - (np.std(non_missing_counts) / expected_uniform_count)
                    if expected_uniform_count > 0
                    else 0.0
                )
                col_result["uniformity"] = max(0.0, min(1.0, float(uniformity)))

        else:
            data_array = tsf.to_numpy()
            col_idx = list(tsf.columns).index(col) if col in tsf.columns else None

            if col_idx is not None and col_idx < data_array.shape[1]:
                col_data = data_array[:, col_idx]
                valid_data = col_data[col_data != -1.0]
                unique_values, counts = np.unique(valid_data, return_counts=True)

                col_result["cardinality"] = len(unique_values)
                col_result["total_count"] = len(col_data)
                col_result["missing_count"] = int(np.sum(col_data == -1.0))
                col_result["non_missing_count"] = len(valid_data)

                sorted_indices = np.argsort(counts)[::-1]
                top_counts = []
                for i in sorted_indices[:10]:
                    top_counts.append(
                        {
                            "value": f"encoded_{int(unique_values[i])}",
                            "count": int(counts[i]),
                        }
                    )
                col_result["top_counts"] = top_counts
                col_result["entropy"] = (
                    _compute_entropy(counts) if len(counts) > 0 else 0.0
                )

            else:
                col_result = {
                    "error": f"Column '{col}' not found in data array",
                    "cardinality": 0,
                    "total_count": 0,
                    "missing_count": 0,
                    "non_missing_count": 0,
                    "top_counts": [],
                    "entropy": 0.0,
                }

        results[col] = col_result

    return results
