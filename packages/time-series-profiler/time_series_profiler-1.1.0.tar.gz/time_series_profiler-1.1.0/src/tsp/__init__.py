from .config import Config
from .profiling import metrics
from .profiling.report import ProfileReport

__version__ = "1.1.0"
__all__ = ["ProfileReport", "Config", "metrics"]
