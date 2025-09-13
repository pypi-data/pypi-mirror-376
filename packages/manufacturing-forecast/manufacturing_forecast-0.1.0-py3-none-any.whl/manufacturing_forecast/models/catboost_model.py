import warnings
warnings.filterwarnings('ignore')

import numpy as np
import shap

try:
    from catboost import CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    # Create a placeholder class for when CatBoost is not available
    class CatBoostRegressor:
        pass

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from .base import BaseRegression


class CatBoostRegression(BaseRegression):
    def __init__(self, **cb_params):
        super().__init__()
        self.cb_params = {
            "iterations": 100,
            "learning_rate": 0.1,
            "depth": 6,
            "random_state": 42,
            "verbose": False,
            **cb_params,
        }
        # Store initialization parameters for cross-validation
        self._init_params = self.cb_params.copy()

    def fit(self, X, y):
        """Fit the CatBoost regression model"""
        if not CATBOOST_AVAILABLE:
            raise ImportError("CatBoost is not installed. Please install it with: pip install catboost")
        if y.ndim > 1 and y.shape[1] > 1:
            # Multi-output regression
            self.model = []
            for i in range(y.shape[1]):
                model_i = CatBoostRegressor(**self.cb_params)
                model_i.fit(X, y[:, i])
                self.model.append(model_i)
        else:
            # Single output regression
            self.model = CatBoostRegressor(**self.cb_params)
            if y.ndim > 1:
                y = y.ravel()
            self.model.fit(X, y)

    def predict(self, X):
        """Make predictions with the fitted model"""
        if not CATBOOST_AVAILABLE:
            raise ImportError("CatBoost is not installed. Please install it with: pip install catboost")
        if self.model is None:
            raise ValueError("Model not fitted yet")

        if isinstance(self.model, list):
            # Multi-output predictions
            predictions = []
            for model_i in self.model:
                pred_i = model_i.predict(X)
                predictions.append(pred_i)
            y_pred = np.column_stack(predictions)
        else:
            # Single output prediction
            y_pred = self.model.predict(X)

        return y_pred

    def evaluate(self, X, y):
        """Evaluate model performance with various metrics"""
        if not CATBOOST_AVAILABLE:
            raise ImportError("CatBoost is not installed. Please install it with: pip install catboost")
        y_pred = self.predict(X)

        if y.ndim == 1:
            y = y.reshape(-1, 1)
        if y_pred.ndim == 1:
            y_pred = y_pred.reshape(-1, 1)

        metrics = {}
        for i in range(y.shape[1]):
            rmse = np.sqrt(mean_squared_error(y[:, i], y_pred[:, i]))
            mae = mean_absolute_error(y[:, i], y_pred[:, i])
            r2 = r2_score(y[:, i], y_pred[:, i])

            metrics[f"output_{i}"] = {"RMSE": rmse, "MAE": mae, "R2": r2}

        return metrics

    def get_shap_values(self, X, background=None):
        """Get SHAP values for feature importance"""
        if not CATBOOST_AVAILABLE:
            raise ImportError("CatBoost is not installed. Please install it with: pip install catboost")
        if self.model is None:
            raise ValueError("Model not fitted yet")

        if isinstance(self.model, list):
            # Multi-output case
            shap_values = []
            for model_i in self.model:
                explainer = shap.TreeExplainer(model_i)
                shap_vals_i = explainer.shap_values(X)
                shap_values.append(shap_vals_i)
            return shap_values
        else:
            # Single output case
            explainer = shap.TreeExplainer(self.model)
            return explainer.shap_values(X)


def train_and_evaluate(X, y, test_size=0.2, random_state=42):
    """Train model and return evaluation metrics"""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    model = CatBoostRegression()
    model.fit(X_train, y_train)

    train_metrics = model.evaluate(X_train, y_train)
    test_metrics = model.evaluate(X_test, y_test)

    return model, train_metrics, test_metrics


if __name__ == "__main__":
    # Example usage
    from sklearn.datasets import make_regression

    X, y = make_regression(
        n_samples=1000, n_features=5, n_targets=2, noise=0.1, random_state=42
    )

    model, train_metrics, test_metrics = train_and_evaluate(X, y)

    print("Training metrics:", train_metrics)
    print("Test metrics:", test_metrics)

    # Save and load example
    model.save("catboost_model.pkl")
    loaded_model = CatBoostRegression.load("catboost_model.pkl")
    print(
        "Loaded model predictions match:",
        np.allclose(model.predict(X[:5]), loaded_model.predict(X[:5])),
    )
