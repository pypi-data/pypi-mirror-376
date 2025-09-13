from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Config:
    backend: str = "pandas"
    time_col: str | None = None
    entity_cols: tuple[str, ...] = ()
    metrics: list[str] | None = None
    sample_rows: int | None = None
    parallel: bool = False
    max_groups: int | None = None

    def __post_init__(self) -> None:
        if self.metrics is None:
            self.metrics = ["basic_stats", "gaps_sampling", "categorical_profile"]

        if not isinstance(self.entity_cols, tuple):
            self.entity_cols = tuple(self.entity_cols)
