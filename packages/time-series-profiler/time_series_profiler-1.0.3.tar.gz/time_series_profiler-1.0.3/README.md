# Time Series Profiler

[![PyPI version](https://badge.fury.io/py/time-series-profiler.svg)](https://badge.fury.io/py/time-series-profiler)
[![Python versions](https://img.shields.io/pypi/pyversions/time-series-profiler.svg)](https://pypi.org/project/time-series-profiler/)
[![CI](https://github.com/adilsaid/time-series-profiler/workflows/CI/badge.svg)](https://github.com/adilsaid/time-series-profiler/actions)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Analyze time-series data structure, gaps, and statistical properties.

## Features

- Basic statistics (mean, std, min, max, percentiles)
- Gap detection and sampling analysis
- Categorical column profiling
- Multi-entity data support
- JSON and HTML output

## Installation

### From PyPI (Recommended)
```bash
pip install time-series-profiler
```

### From Source
```bash
git clone https://github.com/adilsaid/time-series-profiler.git
cd time-series-profiler
pip install -e .
```

## Usage

```python
import pandas as pd
from tsp import ProfileReport, Config

# With DatetimeIndex
df = pd.DataFrame({
    'value': [1.0, 2.5, 3.2, 4.1],
    'category': ['A', 'B', 'A', 'C']
}, index=pd.date_range('2023-01-01', periods=4, freq='1H'))

report = ProfileReport(df, Config())
print(report.to_json())

# With time column and multiple entities
df = pd.read_csv("data.csv", parse_dates=["time"])
config = Config(time_col="time", entity_cols=("user_id",))
report = ProfileReport(df, config)

print(report.to_json())
html_output = report.to_html()
```

### Example

```bash
cd examples
python quickstart.py
```

## License

Apache-2.0 - see LICENSE file for details.
