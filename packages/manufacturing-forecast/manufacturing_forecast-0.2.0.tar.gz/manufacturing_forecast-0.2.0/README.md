# Manufacturing Forecast Package

A Python package for machine learning and data processing methods for manufacturing forecasting applications.

## Features

- Multiple ML regression models (XGBoost, LightGBM, Random Forest, CatBoost, PLS)
- Time series data processing utilities
- Model factory pattern for dynamic model creation
- Cross-validation with time series splits
- SHAP explainability support
- PyPI package structure

## Installation

```bash
pip install manufacturing-forecast
```

## Quick Start

```python
from manufacturing_forecast.models import XGBoostRegression, ModelFactory
from manufacturing_forecast.data import TimeSeriesProcessor

# Create and train a model
model = XGBoostRegression()
model.fit(X_train, y_train)

# Make predictions  
predictions = model.predict(X_test)

# Process time series data
processor = TimeSeriesProcessor()
X, Y = processor.create_lag_lead_matrices(past, target, future, status, lag=10, lead=5)
```

