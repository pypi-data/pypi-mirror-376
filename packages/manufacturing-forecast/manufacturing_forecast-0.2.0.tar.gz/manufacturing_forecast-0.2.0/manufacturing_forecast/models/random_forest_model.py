import warnings
warnings.filterwarnings('ignore')

import numpy as np
import shap
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor

from .base import BaseRegression


class RandomForestRegression(BaseRegression):
    def __init__(self, **rf_params):
        super().__init__()
        self.rf_params = {
            "n_estimators": 100,
            "random_state": 42,
            **rf_params,
        }
        # Store initialization parameters for cross-validation
        self._init_params = self.rf_params.copy()

    def fit(self, X, y):
        """Fit the Random Forest regression model"""
        if y.ndim > 1 and y.shape[1] > 1:
            # Multi-output regression
            self.model = MultiOutputRegressor(RandomForestRegressor(**self.rf_params))
        else:
            # Single output regression
            self.model = RandomForestRegressor(**self.rf_params)

        self.model.fit(X, y)

    def predict(self, X):
        """Make predictions with the fitted model"""
        if self.model is None:
            raise ValueError("Model not fitted yet")

        return self.model.predict(X)

    def evaluate(self, X, y):
        """Evaluate model performance with various metrics"""
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
        if self.model is None:
            raise ValueError("Model not fitted yet")
        
        if isinstance(self.model, MultiOutputRegressor):
            # Multi-output case
            shap_values = []
            for estimator in self.model.estimators_:
                explainer = shap.TreeExplainer(estimator)
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

    model = RandomForestRegression()
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
    model.save("rf_model.pkl")
    loaded_model = RandomForestRegression.load("rf_model.pkl")
    print(
        "Loaded model predictions match:",
        np.allclose(model.predict(X[:5]), loaded_model.predict(X[:5])),
    )
