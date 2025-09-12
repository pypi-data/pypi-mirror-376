from __future__ import annotations

import traceback
from typing import Any

from ..types import TimeSeriesFrame
from .registry import get_metric


def run_metrics(tsf: TimeSeriesFrame, metric_names: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"groups": {}, "summary": {}}

    group_count = 0

    for group_key, group_tsf in tsf.iter_groups():
        group_count += 1
        group_key_str = str(group_key)

        group_results = {}

        for metric_name in metric_names:
            try:
                metric_func = get_metric(metric_name)
                metric_result = metric_func(group_tsf)
                group_results[metric_name] = metric_result
            except Exception as e:
                group_results[metric_name] = {
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }

        result["groups"][group_key_str] = group_results

    if group_count > 1:
        result["summary"]["n_groups"] = group_count

    return result
