"""
Tests for data processing module.
"""

import numpy as np
import pytest

from manufacturing_forecast.data import TimeSeriesProcessor, DataConverter


class TestTimeSeriesProcessor:
    def test_create_lag_lead_matrices(self):
        # Generate sample time series data
        n_timesteps = 50
        past = np.random.randn(2, n_timesteps)  # 2 past features
        target = np.sin(np.linspace(0, 2*np.pi, n_timesteps))
        future = np.random.randn(1, n_timesteps)  # 1 future feature
        status = np.ones(n_timesteps)  # All active
        
        processor = TimeSeriesProcessor()
        X, Y = processor.create_lag_lead_matrices(
            past=past,
            target=target, 
            future=future,
            status=status,
            lag=10,
            lead=5
        )
        
        assert X.shape[0] == Y.shape[0]  # Same number of samples
        assert Y.shape[1] == 5  # Lead steps
        assert X.shape[1] == 2*10 + 1*5  # past_features*lag + future_features*lead
    
    def test_prepare_prediction_features(self):
        processor = TimeSeriesProcessor()
        past_data = np.array([[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]])  # 2 features, 5 timesteps
        future_data = np.array([[0.1, 0.2, 0.3]])  # 1 feature, 3 timesteps
        
        features = processor.prepare_prediction_features(past_data, future_data, lag=3)
        
        expected_length = 2 * 3 + 1 * 3  # 2 past features * 3 lags + 1 future feature * 3 timesteps
        assert features.shape == (1, expected_length)
    
    def test_empty_input_handling(self):
        processor = TimeSeriesProcessor()
        
        # Test with insufficient data
        past = np.random.randn(1, 5)  # Only 5 timesteps
        target = np.random.randn(5)
        future = np.random.randn(1, 5)
        status = np.ones(5)
        
        X, Y = processor.create_lag_lead_matrices(past, target, future, status, lag=10, lead=5)
        
        # Should return empty arrays when not enough data
        assert X.size == 0
        assert Y.size == 0


class TestDataConverter:
    def test_to_numpy_basic(self):
        # Mock data object
        class MockData:
            def __init__(self):
                self.Results = {
                    'series1': [{'value': 1.0}, {'value': 2.0}, {'value': 3.0}],
                    'series2': [{'value': 4.0}, {'value': 5.0}, {'value': 6.0}]
                }
        
        mock_data = MockData()
        result = DataConverter.to_numpy(mock_data)
        
        expected = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        np.testing.assert_array_equal(result, expected)
    
    def test_from_dataframe(self):
        # Test requires pandas, skip if not available
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not available")
        
        df = pd.DataFrame({
            'target_col': [1, 2, 3, 4, 5],
            'past1': [6, 7, 8, 9, 10], 
            'past2': [11, 12, 13, 14, 15],
            'future1': [16, 17, 18, 19, 20]
        })
        
        column_mapping = {
            'target': ['target_col'],
            'past': ['past1', 'past2'],
            'future': ['future1'],
            'status': []
        }
        
        result = DataConverter.from_dataframe(df, column_mapping)
        
        assert 'target' in result
        assert 'past' in result
        assert 'future' in result
        assert result['target'].shape == (5,)
        assert result['past'].shape == (2, 5)  # 2 features, 5 timesteps
        assert result['future'].shape == (5,)


if __name__ == "__main__":
    pytest.main([__file__])
