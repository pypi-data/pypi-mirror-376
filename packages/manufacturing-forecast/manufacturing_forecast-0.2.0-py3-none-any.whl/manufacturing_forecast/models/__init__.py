"""
ML Models module with factory pattern for model creation and management.
"""
from .base import BaseRegression
from .factory import ModelFactory, ModelRegistry
from .xgboost_model import XGBoostRegression
from .lightgbm_model import LightGBMRegression
from .random_forest_model import RandomForestRegression
from .catboost_model import CatBoostRegression
from .pls_model import PLSRegression

# Register models with the factory
ModelRegistry.register("xgboost", XGBoostRegression)
ModelRegistry.register("lightgbm", LightGBMRegression)
ModelRegistry.register("random_forest", RandomForestRegression)
ModelRegistry.register("catboost", CatBoostRegression)
ModelRegistry.register("pls", PLSRegression)

__all__ = [
    "BaseRegression",
    "ModelFactory",
    "ModelRegistry",
    "XGBoostRegression",
    "LightGBMRegression",
    "RandomForestRegression",
    "CatBoostRegression",
    "PLSRegression",
]
