"""
Manufacturing Forecast Package

A Python package for machine learning and data processing methods for manufacturing forecasting applications.
"""

__version__ = "0.2.0"
__author__ = "Manufacturing Forecast Team"
__email__ = "contact@example.com"

from .data import (
    AssetConverter,
    DataConverter,
    TimeSeriesProcessor,
)
from .models import (
    BaseRegression,
    CatBoostRegression,
    LightGBMRegression,
    ModelFactory,
    ModelRegistry,
    PLSRegression,
    RandomForestRegression,
    XGBoostRegression,
)

__all__ = [
    # Models
    "BaseRegression",
    "ModelFactory",
    "ModelRegistry",
    "XGBoostRegression",
    "LightGBMRegression",
    "RandomForestRegression",
    "CatBoostRegression",
    "PLSRegression",
    # Data processing
    "TimeSeriesProcessor",
    "AssetConverter",
    "DataConverter",
]
