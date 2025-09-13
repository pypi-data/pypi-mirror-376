from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..types import TimeSeriesFrame

_REGISTRY: dict[str, Callable[[TimeSeriesFrame], dict[str, Any]]] = {}


def register(name: str) -> Callable:
    def decorator(
        func: Callable[[TimeSeriesFrame], dict[str, Any]],
    ) -> Callable[[TimeSeriesFrame], dict[str, Any]]:
        _REGISTRY[name] = func
        return func

    return decorator


def get_metric(name: str) -> Callable[[TimeSeriesFrame], dict[str, Any]]:
    if name not in _REGISTRY:
        raise KeyError(
            f"Metric '{name}' not found. Available metrics: {list(_REGISTRY.keys())}"
        )
    return _REGISTRY[name]


def list_metrics() -> list[str]:
    return list(_REGISTRY.keys())
