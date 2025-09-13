"""
Manufacturing Forecast Package

A Python package for machine learning and data processing methods for manufacturing forecasting applications.
"""

__version__ = "0.1.0"
__author__ = "Manufacturing Forecast Team"
__email__ = "contact@example.com"

from .models import (
    BaseRegression,
    ModelFactory,
    ModelRegistry,
    XGBoostRegression,
    LightGBMRegression,
    RandomForestRegression,
    CatBoostRegression,
    PLSRegression,
)

from .data import (
    TimeSeriesProcessor,
    AssetConverter,
    DataConverter,
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
