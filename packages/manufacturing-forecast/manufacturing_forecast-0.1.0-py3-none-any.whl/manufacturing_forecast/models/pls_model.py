import warnings
warnings.filterwarnings('ignore')

import numpy as np
import shap
from sklearn.cross_decomposition import PLSRegression as SklearnPLSRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from .base import BaseRegression


class PLSRegression(BaseRegression):
    def __init__(self, n_components=2, scale_features=True):
        super().__init__()
        self.model = SklearnPLSRegression(n_components=n_components)
        self.scaler_X = StandardScaler() if scale_features else None
        self.scaler_y = StandardScaler() if scale_features else None
        self.scale_features = scale_features
        # Store initialization parameters for cross-validation
        self._init_params = {'n_components': n_components, 'scale_features': scale_features}

    def fit(self, X, y):
        """Fit the PLS regression model with optional scaling"""
        if self.scale_features:
            X_scaled = self.scaler_X.fit_transform(X)
            y_scaled = self.scaler_y.fit_transform(y)
            self.model.fit(X_scaled, y_scaled)
        else:
            self.model.fit(X, y)

    def predict(self, X):
        """Make predictions with the fitted model"""
        if self.scale_features:
            X_scaled = self.scaler_X.transform(X)
            y_pred_scaled = self.model.predict(X_scaled)
            return self.scaler_y.inverse_transform(y_pred_scaled)
        else:
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

        if background is None:
            background = X[:100] if len(X) > 100 else X

        explainer = shap.KernelExplainer(self.predict, background)
        shap_values = explainer.shap_values(X)

        return shap_values


def train_and_evaluate(X, y, test_size=0.2, random_state=42):
    """Train model and return evaluation metrics"""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    model = PLSRegression(scale_features=True)
    model.fit(X_train, y_train)

    train_metrics = model.evaluate(X_train, y_train)
    test_metrics = model.evaluate(X_test, y_test)

    return model, train_metrics, test_metrics
