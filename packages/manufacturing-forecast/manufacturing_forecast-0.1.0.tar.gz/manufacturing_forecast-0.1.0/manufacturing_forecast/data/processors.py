"""
Time series data processors for ML model input preparation.
"""

from typing import Optional, Tuple

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


class TimeSeriesProcessor:
    """Processor for time series data transformations"""

    @staticmethod
    def create_lag_lead_matrices(
        past: np.ndarray,
        target: np.ndarray,
        future: np.ndarray,
        status: np.ndarray,
        lag: int,
        lead: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create lag-lead matrices for time series ML models.

        Args:
            past: numpy array of shape (n_past_features, n_timesteps)
            target: numpy array of shape (n_timesteps,) - target variable
            future: numpy array of shape (n_future_features, n_timesteps)
            status: numpy array of shape (n_timesteps,) - filter array (1=ON, 0=OFF)
            lag: int - number of lagged timesteps to include
            lead: int - number of future timesteps to predict

        Returns:
            Tuple[np.ndarray, np.ndarray]: Feature matrix X and target matrix Y
        """
        # Ensure target and status are 1D arrays
        target = np.asarray(target).flatten()
        status = np.asarray(status).flatten()

        # Handle empty or single-dimensional inputs
        if past.ndim == 1:
            past = past.reshape(1, -1)
        if future.ndim == 1:
            future = future.reshape(1, -1)

        n_timesteps = len(target)

        # Check if we have sufficient data for lag features
        # If any past feature doesn't have enough data for lag, return empty
        for feature in past:
            if len(feature) < lag:
                return np.array([]), np.array([])
        
        # Create sliding windows for past features
        past_windows = []
        for feature in past:
            window = sliding_window_view(feature, window_shape=lag)
            past_windows.append(window)

        # Create sliding windows for future features
        future_windows = []
        for feature in future:
            if len(feature) >= lead:
                window = sliding_window_view(feature, window_shape=lead)
                future_windows.append(window)

        # Create target sliding window
        if len(target) >= lead:
            target_window = sliding_window_view(target, window_shape=lead)
        else:
            return np.array([]), np.array([])

        # Align windows considering both lag and lead
        min_samples = min(
            len(past_windows[0]) if past_windows else n_timesteps,
            len(future_windows[0]) if future_windows else n_timesteps,
            len(target_window),
        )

        if min_samples <= 0:
            return np.array([]), np.array([])

        # Combine features
        X_list = []

        # Add past features
        for window in past_windows:
            X_list.append(window[:min_samples])

        # Add future features
        for window in future_windows:
            X_list.append(window[:min_samples])

        # Stack features
        if X_list:
            X = np.hstack(X_list)
        else:
            X = np.array([])

        # Prepare target
        Y = target_window[:min_samples]

        # Apply status filter if provided and we have sufficient data
        if len(status) > 0 and len(status) >= lag and min_samples > 0:
            # Create status window for filtering
            status_window = sliding_window_view(status, window_shape=lag)[:min_samples]
            valid_indices = np.all(status_window == 1, axis=1)

            if X.size > 0:
                X = X[valid_indices]
            Y = Y[valid_indices]

        return X, Y

    @staticmethod
    def prepare_prediction_features(
        past_data: np.ndarray, future_data: Optional[np.ndarray] = None, lag: int = 1
    ) -> np.ndarray:
        """
        Prepare features for prediction from recent data.

        Args:
            past_data: Recent past data for lagged features
            future_data: Optional future covariates
            lag: Number of lagged timesteps

        Returns:
            np.ndarray: Prepared feature vector
        """
        features = []

        # Add lagged past features
        if past_data.ndim == 1:
            past_data = past_data.reshape(1, -1)

        for feature in past_data:
            if len(feature) >= lag:
                features.extend(feature[-lag:])

        # Add future features if provided
        if future_data is not None:
            if future_data.ndim == 1:
                future_data = future_data.reshape(1, -1)

            for feature in future_data:
                features.extend(feature)

        return np.array(features).reshape(1, -1)
