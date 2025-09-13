import pickle
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error


class BaseRegression(ABC):
    """Abstract base class for regression models with save/load functionality"""

    def __init__(self):
        self.model = None
        self._init_params = {}

    @abstractmethod
    def fit(self, X, y):
        """Fit the regression model"""
        pass

    @abstractmethod
    def predict(self, X):
        """Make predictions with the fitted model"""
        pass

    @abstractmethod
    def evaluate(self, X, y):
        """Evaluate model performance with various metrics"""
        pass

    @abstractmethod
    def get_shap_values(self, X, background=None):
        """Get SHAP values for feature importance"""
        pass

    def save(self, filepath):
        """Save the model to a pickle file"""
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    def fit_and_save(self, X, y, filepath):
        """Fit the model and save it to a file"""
        self.fit(X, y)
        self.save(filepath)

    @classmethod
    def load(cls, filepath):
        """Load a model from a pickle file"""
        with open(filepath, "rb") as f:
            return pickle.load(f)
    
    def cross_validate(self, X: np.ndarray, y: np.ndarray, lag: int, lead: int, 
                      n_splits: int = 20, gap: int = 0, test_ratio: float = 0.05) -> Dict[str, Any]:
        """
        Perform time series cross-validation with 95:5 train-test split and lag+lead segments.
        
        Args:
            X: Feature matrix of shape (n_samples, n_features)
            y: Target matrix of shape (n_samples, n_outputs) or (n_samples,)
            lag: Number of lag timesteps used for features
            lead: Number of lead timesteps for predictions
            n_splits: Number of cross-validation splits (default: 20)
            gap: Gap between train and test sets (to prevent data leakage)
            test_ratio: Ratio of data to use for testing in each fold (default: 0.05 for 5%)
        
        Returns:
            Dictionary containing cross-validation metrics and predictions
        """
        if X.shape[0] != y.shape[0]:
            raise ValueError("X and y must have the same number of samples")
        
        n_samples = X.shape[0]
        segment_size = lag + lead  # Each fold considers lag+lead window
        
        # Calculate test size based on ratio
        test_size = max(segment_size, int(n_samples * test_ratio))
        
        # Ensure we have enough data for cross-validation
        min_samples_per_split = test_size + gap + segment_size  # minimum for train data
        if n_samples < min_samples_per_split:
            raise ValueError(f"Not enough samples for cross-validation with test_ratio={test_ratio}. "
                           f"Need at least {min_samples_per_split} samples, got {n_samples}")
        
        # Standardize y to 2D array
        if y.ndim == 1:
            y = y.reshape(-1, 1)
            single_output = True
        else:
            single_output = False
        
        n_outputs = y.shape[1]
        
        # Initialize result containers
        cv_results = {
            'train_scores': [],
            'test_scores': [],
            'fold_metrics': [],
            'predictions': [],
            'test_indices': [],
            'feature_importance': [],
            'segment_size': segment_size,
            'n_splits': n_splits,
            'gap': gap,
            'test_ratio': test_ratio,
            'test_size': test_size
        }
        
        # Calculate available range for test set starting positions
        max_test_start = n_samples - test_size - gap
        if max_test_start <= 0:
            raise ValueError("Dataset too small for the specified test ratio and gap")
        
        # Generate test start positions for n_splits folds
        test_starts = np.linspace(0, max_test_start, n_splits, dtype=int)
        
        for fold, test_start in enumerate(test_starts):
            # Define test set indices for this fold
            test_end = test_start + test_size
            test_indices = list(range(test_start, test_end))
            
            # Define train indices (everything except test + gap) - 95% of data
            train_indices = []
            
            # Add samples before the test set (with gap)
            if test_start - gap > 0:
                train_indices.extend(range(0, test_start - gap))
            
            # Add samples after the test set (with gap)
            if test_end + gap < n_samples:
                train_indices.extend(range(test_end + gap, n_samples))
            
            # Skip if not enough training data
            if len(train_indices) < segment_size:
                continue
            
            # Create train/test splits
            X_train, X_test = X[train_indices], X[test_indices]
            y_train, y_test = y[train_indices], y[test_indices]
            
            # Create a copy of the model for this fold
            fold_model = self.__class__(**getattr(self, '_init_params', {}))
            
            # Fit model on training data
            fold_model.fit(X_train, y_train)
            
            # Make predictions
            y_train_pred = fold_model.predict(X_train)
            y_test_pred = fold_model.predict(X_test)
            
            # Ensure predictions are 2D
            if y_train_pred.ndim == 1:
                y_train_pred = y_train_pred.reshape(-1, 1)
            if y_test_pred.ndim == 1:
                y_test_pred = y_test_pred.reshape(-1, 1)
            
            # Calculate metrics for this fold
            train_metrics = self._calculate_cv_metrics(y_train, y_train_pred)
            test_metrics = self._calculate_cv_metrics(y_test, y_test_pred)
            
            # Store results
            cv_results['train_scores'].append(train_metrics)
            cv_results['test_scores'].append(test_metrics)
            cv_results['predictions'].append({
                'y_true': y_test,
                'y_pred': y_test_pred,
                'test_indices': test_indices
            })
            cv_results['test_indices'].append(test_indices)
            
            # Try to get feature importance if available
            try:
                if hasattr(fold_model, 'model'):
                    if isinstance(fold_model.model, list):
                        # Multi-output case
                        importance = [getattr(m, 'feature_importances_', None) for m in fold_model.model]
                    else:
                        # Single output case
                        importance = getattr(fold_model.model, 'feature_importances_', None)
                    cv_results['feature_importance'].append(importance)
            except:
                pass
            
            cv_results['fold_metrics'].append({
                'fold': fold,
                'train_size': len(train_indices),
                'test_size': len(test_indices),
                'test_start': test_start,
                'test_end': test_end,
                'train_metrics': train_metrics,
                'test_metrics': test_metrics
            })
        
        # Calculate summary statistics
        cv_results['mean_train_scores'] = self._calculate_mean_metrics(cv_results['train_scores'])
        cv_results['mean_test_scores'] = self._calculate_mean_metrics(cv_results['test_scores'])
        cv_results['std_train_scores'] = self._calculate_std_metrics(cv_results['train_scores'])
        cv_results['std_test_scores'] = self._calculate_std_metrics(cv_results['test_scores'])
        
        return cv_results
    
    def _calculate_cv_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Dict[str, float]]:
        """
        Calculate comprehensive metrics for cross-validation.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            
        Returns:
            Dictionary of metrics per output
        """
        metrics = {}
        
        for i in range(y_true.shape[1]):
            y_true_i = y_true[:, i]
            y_pred_i = y_pred[:, i]
            
            # Basic regression metrics
            rmse = np.sqrt(mean_squared_error(y_true_i, y_pred_i))
            mae = mean_absolute_error(y_true_i, y_pred_i)
            r2 = r2_score(y_true_i, y_pred_i)
            
            # Additional metrics
            mse = mean_squared_error(y_true_i, y_pred_i)
            
            # MAPE (handle division by zero)
            try:
                mape = mean_absolute_percentage_error(y_true_i, y_pred_i)
            except:
                mape = np.inf if np.any(y_true_i == 0) else np.mean(np.abs((y_true_i - y_pred_i) / y_true_i)) * 100
            
            # Additional custom metrics
            max_error = np.max(np.abs(y_true_i - y_pred_i))
            
            # Directional accuracy (for time series)
            if len(y_true_i) > 1:
                true_direction = np.diff(y_true_i) > 0
                pred_direction = np.diff(y_pred_i) > 0
                directional_accuracy = np.mean(true_direction == pred_direction) * 100
            else:
                directional_accuracy = np.nan
            
            # Normalized metrics
            y_range = np.max(y_true_i) - np.min(y_true_i)
            normalized_rmse = rmse / y_range if y_range > 0 else np.inf
            normalized_mae = mae / y_range if y_range > 0 else np.inf
            
            metrics[f'output_{i}'] = {
                'RMSE': rmse,
                'MAE': mae,
                'MSE': mse,
                'R2': r2,
                'MAPE': mape,
                'Max_Error': max_error,
                'Directional_Accuracy': directional_accuracy,
                'Normalized_RMSE': normalized_rmse,
                'Normalized_MAE': normalized_mae,
                'Mean_True': np.mean(y_true_i),
                'Mean_Pred': np.mean(y_pred_i),
                'Std_True': np.std(y_true_i),
                'Std_Pred': np.std(y_pred_i)
            }
        
        return metrics
    
    def _calculate_mean_metrics(self, metrics_list: List[Dict]) -> Dict[str, Dict[str, float]]:
        """
        Calculate mean of metrics across folds.
        """
        if not metrics_list:
            return {}
        
        mean_metrics = {}
        for output_key in metrics_list[0].keys():
            mean_metrics[output_key] = {}
            for metric_name in metrics_list[0][output_key].keys():
                values = [fold_metrics[output_key][metric_name] for fold_metrics in metrics_list 
                         if not np.isnan(fold_metrics[output_key][metric_name]) and not np.isinf(fold_metrics[output_key][metric_name])]
                mean_metrics[output_key][metric_name] = np.mean(values) if values else np.nan
        
        return mean_metrics
    
    def _calculate_std_metrics(self, metrics_list: List[Dict]) -> Dict[str, Dict[str, float]]:
        """
        Calculate standard deviation of metrics across folds.
        """
        if not metrics_list:
            return {}
        
        std_metrics = {}
        for output_key in metrics_list[0].keys():
            std_metrics[output_key] = {}
            for metric_name in metrics_list[0][output_key].keys():
                values = [fold_metrics[output_key][metric_name] for fold_metrics in metrics_list 
                         if not np.isnan(fold_metrics[output_key][metric_name]) and not np.isinf(fold_metrics[output_key][metric_name])]
                std_metrics[output_key][metric_name] = np.std(values) if values else np.nan
        
        return std_metrics
