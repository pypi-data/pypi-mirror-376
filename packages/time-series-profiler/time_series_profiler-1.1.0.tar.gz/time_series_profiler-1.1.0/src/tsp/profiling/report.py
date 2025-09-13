from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from jinja2 import Template

from ..adapters import wrap
from ..config import Config
from ..types import TimeSeriesFrame
from .runner import run_metrics


class ProfileReport:
    def __init__(self, data: Any, config: Config):
        self.data = data
        self.config = config
        self._tsf: TimeSeriesFrame | None = None
        self._results: dict[str, Any] | None = None

    def _wrap(self) -> TimeSeriesFrame:
        if self._tsf is None:
            if self.config.backend == "pandas":
                self._tsf = wrap(
                    self.data,
                    time_col=self.config.time_col,
                    entity_cols=self.config.entity_cols,
                )
            else:
                raise ValueError(f"Unsupported backend: {self.config.backend}")
        return self._tsf

    def compute(self) -> dict[str, Any]:
        if self._results is None:
            tsf = self._wrap()

            results = run_metrics(tsf, self.config.metrics)

            self._results = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "config": {
                        "backend": self.config.backend,
                        "time_col": self.config.time_col,
                        "entity_cols": self.config.entity_cols,
                        "metrics": self.config.metrics,
                    },
                },
                **results,
            }

        return self._results

    def to_json(self, indent: int = 2) -> str:
        results = self.compute()
        return json.dumps(results, indent=indent, default=str)

    def to_html(self, title: str = "Time Series Profile Report") -> str:
        results = self.compute()

        # Simple HTML template
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .group { border: 1px solid #ddd; margin: 10px 0; padding: 10px; border-radius: 5px; }
        .metric { margin: 10px 0; }
        .metric-name { font-weight: bold; color: #333; }
        pre { background-color: #f8f8f8; padding: 10px; border-radius: 3px; overflow-x: auto; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p><strong>Generated:</strong> {{ metadata.timestamp }}</p>
        <p><strong>Backend:</strong> {{ metadata.config.backend }}</p>
        {% if metadata.config.time_col %}
        <p><strong>Time Column:</strong> {{ metadata.config.time_col }}</p>
        {% endif %}
        {% if metadata.config.entity_cols %}
        <p><strong>Entity Columns:</strong> {{ metadata.config.entity_cols|join(', ') }}</p>
        {% endif %}
    </div>

    {% if summary.n_groups %}
    <div class="section">
        <h2>Summary</h2>
        <p><strong>Number of Groups:</strong> {{ summary.n_groups }}</p>
    </div>
    {% endif %}

    <div class="section">
        <h2>Profile Results</h2>
        {% for group_key, group_data in groups.items() %}
        <div class="group">
            <h3>Group: {{ group_key }}</h3>
            {% for metric_name, metric_data in group_data.items() %}
            <div class="metric">
                <div class="metric-name">{{ metric_name }}</div>
                {% if metric_data.error %}
                <p style="color: red;"><strong>Error:</strong> {{ metric_data.error }}</p>
                {% else %}
                <pre>{{ metric_data|tojson(indent=2) }}</pre>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </div>
</body>
</html>
        """

        template = Template(template_str)

        # Convert results to JSON-serializable format for template
        json_safe_results = json.loads(json.dumps(results, default=str))

        return template.render(
            title=title,
            metadata=json_safe_results["metadata"],
            summary=json_safe_results.get("summary", {}),
            groups=json_safe_results["groups"],
        )
