"""
Tests for data processing module.
"""

import numpy as np
import pytest

from manufacturing_forecast.data import DataConverter, TimeSeriesProcessor


class TestTimeSeriesProcessor:
    def test_create_lag_lead_matrices(self):
        # Generate sample time series data
        n_timesteps = 50
        past = np.arange(0, 100).reshape(2, 50)  # 2 past features
        target = np.arange(100, 150)
        future = np.arange(150, 200)  # 1 future feature
        status = np.ones(n_timesteps)  # All active

        processor = TimeSeriesProcessor()
        X, Y = processor.create_lag_lead_matrices(
            past=past, target=target, future=future, status=status, lag=10, lead=5
        )

        assert X.shape[0] == Y.shape[0]  # Same number of samples
        assert Y.shape[1] == 5  # Lead steps
        assert (
            X.shape[1] == 2 * 10 + 1 * 10 + 1 * 15
        )  # past_features*lag + target*lag + future_features*(lag+lead)

    def test_prepare_prediction_features(self):
        processor = TimeSeriesProcessor()
        past_data = np.array(
            [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]
        )  # 2 features, 5 timesteps
        future_data = np.array([[0.1, 0.2, 0.3]])  # 1 feature, 3 timesteps

        features = processor.prepare_prediction_features(past_data, future_data, lag=3)

        expected_length = (
            2 * 3 + 1 * 3
        )  # 2 past features * 3 lags + 1 future feature * 3 timesteps
        assert features.shape == (1, expected_length)

    def test_empty_input_handling(self):
        processor = TimeSeriesProcessor()

        # Test with insufficient data
        past = np.random.randn(1, 5)  # Only 5 timesteps
        target = np.random.randn(5)
        future = np.random.randn(1, 5)
        status = np.ones(5)

        X, Y = processor.create_lag_lead_matrices(
            past, target, future, status, lag=10, lead=5
        )

        # Should return empty arrays when not enough data
        assert X.size == 0
        assert Y.size == 0

    def test_create_lag_lead_matrices_without_future(self):
        # Test with only past features and target, no future features
        n_timesteps = 50
        past = np.arange(0, 100).reshape(2, 50)  # 2 past features: [0-49], [50-99]
        target = np.arange(100, 150)  # target: 100-149
        future = np.array([]).reshape(0, 50)  # No future features
        status = np.ones(n_timesteps)  # All active

        processor = TimeSeriesProcessor()
        X, Y = processor.create_lag_lead_matrices(
            past=past, target=target, future=future, status=status, lag=10, lead=5
        )

        assert X.shape[0] == Y.shape[0]  # Same number of samples
        assert Y.shape[1] == 5  # Lead steps
        assert (
            X.shape[1] == 2 * 10 + 1 * 10
        )  # past_features*lag + target*lag (no future)

        # Verify the content of first sample
        if X.size > 0:
            # First 10 values should be past[0] lag
            np.testing.assert_array_equal(X[0, :10], past[0, :10])
            # Next 10 values should be past[1] lag
            np.testing.assert_array_equal(X[0, 10:20], past[1, :10])
            # Next 10 values should be target lag
            np.testing.assert_array_equal(X[0, 20:30], target[:10])
            # Y should be target lead
            np.testing.assert_array_equal(Y[0], target[10:15])

    def test_create_lag_lead_matrices_without_past(self):
        # Test with only target and future features, no past features
        n_timesteps = 50
        past = np.array([]).reshape(0, 50)  # No past features
        target = np.arange(100, 150)  # target: 100-149
        future = np.arange(200, 250).reshape(1, 50)  # 1 future feature: 200-249
        status = np.ones(n_timesteps)  # All active

        processor = TimeSeriesProcessor()
        X, Y = processor.create_lag_lead_matrices(
            past=past, target=target, future=future, status=status, lag=10, lead=5
        )

        assert X.shape[0] == Y.shape[0]  # Same number of samples
        assert Y.shape[1] == 5  # Lead steps
        assert (
            X.shape[1] == 1 * 10 + 1 * 15
        )  # target*lag + future_features*(lag+lead) (no past)

        # Verify the content of first sample
        if X.size > 0:
            # First 10 values should be target lag
            np.testing.assert_array_equal(X[0, :10], target[:10])
            # Next 15 values should be future lag+lead window
            np.testing.assert_array_equal(X[0, 10:25], future[0, :15])
            # Y should be target lead
            np.testing.assert_array_equal(Y[0], target[10:15])

    def test_create_lag_lead_matrices_without_status(self):
        # Test with all features but no status filtering
        n_timesteps = 50
        past = np.arange(0, 100).reshape(2, 50)  # 2 past features: [0-49], [50-99]
        target = np.arange(100, 150)  # target: 100-149
        future = np.arange(200, 250).reshape(1, 50)  # 1 future feature: 200-249
        status = np.array([])  # No status array

        processor = TimeSeriesProcessor()
        X, Y = processor.create_lag_lead_matrices(
            past=past, target=target, future=future, status=status, lag=10, lead=5
        )

        assert X.shape[0] == Y.shape[0]  # Same number of samples
        assert Y.shape[1] == 5  # Lead steps
        assert (
            X.shape[1] == 2 * 10 + 1 * 10 + 1 * 15
        )  # past*lag + target*lag + future*(lag+lead)

        # Should have same results as with all-ones status (no filtering)
        # Verify the content of first sample
        if X.size > 0:
            # First 10 values should be past[0] lag
            np.testing.assert_array_equal(X[0, :10], past[0, :10])
            # Next 10 values should be past[1] lag
            np.testing.assert_array_equal(X[0, 10:20], past[1, :10])
            # Next 10 values should be target lag
            np.testing.assert_array_equal(X[0, 20:30], target[:10])
            # Next 15 values should be future lag+lead window
            np.testing.assert_array_equal(X[0, 30:45], future[0, :15])
            # Y should be target lead
            np.testing.assert_array_equal(Y[0], target[10:15])

    def test_create_lag_lead_matrices_minimal_case(self):
        # Test with only target (no past, no future, no status)
        n_timesteps = 20
        past = np.array([]).reshape(0, 20)  # No past features
        target = np.arange(100, 120)  # target: 100-119 (20 timesteps)
        future = np.array([]).reshape(0, 20)  # No future features
        status = np.array([])  # No status

        processor = TimeSeriesProcessor()
        X, Y = processor.create_lag_lead_matrices(
            past=past, target=target, future=future, status=status, lag=5, lead=3
        )

        assert X.shape[0] == Y.shape[0]  # Same number of samples
        assert Y.shape[1] == 3  # Lead steps
        assert X.shape[1] == 1 * 5  # Only target*lag

        # Should have 12 samples (20 - 5 - 3 = 12 valid windows)
        expected_samples = 20 - 5 - 3 + 1
        assert X.shape[0] == expected_samples

        # Verify the content of first sample
        if X.size > 0:
            # X should contain target lag (100-104)
            np.testing.assert_array_equal(X[0], target[:5])  # 100, 101, 102, 103, 104
            # Y should contain target lead (105-107)
            np.testing.assert_array_equal(Y[0], target[5:8])  # 105, 106, 107

    def test_create_lag_lead_matrices_status_filtering(self):
        # Test status filtering functionality
        n_timesteps = 50
        past = np.arange(0, 100).reshape(2, 50)  # 2 past features: [0-24], [25-49]
        target = np.arange(100, 150)  # target: 100-124
        future = np.arange(150, 250).reshape(1, 100)  # 1 future feature: 200-224

        # Create status with specific pattern for lag=5
        status = np.ones(n_timesteps)
        status[2:5] = 0  # Zeros at positions 2,3,4 (3 consecutive zeros < lag=5)
        status[8:13] = (
            0  # Zeros at positions 8,9,10,11,12 (5 consecutive zeros = lag=5)
        )
        # Status pattern: [1,1,0,0,0,1,1,1,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1]

        processor = TimeSeriesProcessor()
        X, Y = processor.create_lag_lead_matrices(
            past=past, target=target, future=future, status=status, lag=5, lead=3
        )

        # Should have filtered out windows that include the lag=5 period of zeros (positions 8-12)
        assert X.shape[0] == Y.shape[0]
        assert Y.shape[1] == 3  # Lead steps

    def test_create_lag_lead_matrices_status_short_zeros(self):
        # Test that only FULL lag windows of zeros cause filtering (not short periods)
        n_timesteps = 25
        past = np.arange(0, 50).reshape(2, 25)  # 2 past features
        target = np.arange(100, 125)  # target: 100-124
        future = np.arange(200, 225).reshape(1, 25)  # 1 future feature

        # Status with short zero periods (shouldn't filter) and full lag zero period (should filter)
        status = np.ones(25)
        status[3:5] = (
            0  # 2 zeros at positions 3,4 - should NOT cause filtering (< lag=5)
        )
        status[10:15] = (
            0  # 5 zeros at positions 10-14 - should cause filtering (= lag=5)
        )

        processor = TimeSeriesProcessor()
        X, Y = processor.create_lag_lead_matrices(
            past=past, target=target, future=future, status=status, lag=5, lead=3
        )

        # Compare with no filtering
        processor_no_filter = TimeSeriesProcessor()
        X_no_filter, Y_no_filter = processor_no_filter.create_lag_lead_matrices(
            past=past, target=target, future=future, status=np.ones(25), lag=5, lead=3
        )

        # Should have fewer samples since windows with full lag zeros get filtered
        assert X.shape[0] < X_no_filter.shape[0]

        # Verify behavior: short zeros don't filter, but full lag zeros do filter
        # Windows overlapping positions 10-14 (all zeros) should be filtered
        # Windows overlapping positions 3-4 (short zeros) should NOT be filtered
        assert X.shape[0] > 0  # Should have some remaining samples


class TestDataConverter:
    def test_to_numpy_basic(self):
        # Mock data object
        class MockData:
            def __init__(self):
                self.Results = {
                    "series1": [{"value": 1.0}, {"value": 2.0}, {"value": 3.0}],
                    "series2": [{"value": 4.0}, {"value": 5.0}, {"value": 6.0}],
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

        df = pd.DataFrame(
            {
                "target_col": [1, 2, 3, 4, 5],
                "past1": [6, 7, 8, 9, 10],
                "past2": [11, 12, 13, 14, 15],
                "future1": [16, 17, 18, 19, 20],
            }
        )

        column_mapping = {
            "target": ["target_col"],
            "past": ["past1", "past2"],
            "future": ["future1"],
            "status": [],
        }

        result = DataConverter.from_dataframe(df, column_mapping)

        assert "target" in result
        assert "past" in result
        assert "future" in result
        assert result["target"].shape == (5,)
        assert result["past"].shape == (2, 5)  # 2 features, 5 timesteps
        assert result["future"].shape == (5,)


if __name__ == "__main__":
    pytest.main([__file__])
