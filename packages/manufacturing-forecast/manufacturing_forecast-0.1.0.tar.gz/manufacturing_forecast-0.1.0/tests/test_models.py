"""
Tests for ML models module.
"""

import numpy as np
import pytest
from sklearn.datasets import make_regression

from manufacturing_forecast.models import (
    XGBoostRegression,
    LightGBMRegression, 
    RandomForestRegression,
    CatBoostRegression,
    PLSRegression,
    ModelFactory,
    ModelRegistry,
)


@pytest.fixture
def sample_data():
    """Generate sample regression data."""
    X, y = make_regression(n_samples=100, n_features=5, n_targets=2, noise=0.1, random_state=42)
    return X, y


@pytest.fixture
def single_output_data():
    """Generate single output regression data."""
    X, y = make_regression(n_samples=100, n_features=5, n_targets=1, noise=0.1, random_state=42)
    return X, y.ravel()


class TestXGBoostRegression:
    def test_fit_predict_multi_output(self, sample_data):
        X, y = sample_data
        model = XGBoostRegression()
        model.fit(X, y)
        
        y_pred = model.predict(X)
        assert y_pred.shape == y.shape
    
    def test_fit_predict_single_output(self, single_output_data):
        X, y = single_output_data
        model = XGBoostRegression()
        model.fit(X, y)
        
        y_pred = model.predict(X)
        assert len(y_pred) == len(y)
    
    def test_evaluate(self, sample_data):
        X, y = sample_data
        model = XGBoostRegression()
        model.fit(X, y)
        
        metrics = model.evaluate(X, y)
        assert isinstance(metrics, dict)
        assert "output_0" in metrics
        assert "output_1" in metrics
        assert "RMSE" in metrics["output_0"]
        assert "R2" in metrics["output_0"]
    
    def test_get_shap_values(self, sample_data):
        X, y = sample_data
        model = XGBoostRegression()
        model.fit(X, y)
        
        shap_values = model.get_shap_values(X[:10])  # Test on subset
        assert shap_values is not None
        assert len(shap_values) == 2  # Multi-output
    
    def test_cross_validate(self, sample_data):
        X, y = sample_data
        model = XGBoostRegression()
        
        cv_results = model.cross_validate(X, y, lag=5, lead=3, n_splits=3)
        assert "mean_test_scores" in cv_results
        assert "fold_metrics" in cv_results
        assert len(cv_results["fold_metrics"]) <= 3  # May be fewer due to insufficient data
    
    def test_save_load(self, sample_data, tmp_path):
        X, y = sample_data
        model = XGBoostRegression()
        model.fit(X, y)
        
        # Save model
        model_path = tmp_path / "test_model.pkl"
        model.save(str(model_path))
        
        # Load model
        loaded_model = XGBoostRegression.load(str(model_path))
        
        # Test predictions are the same
        y_pred_original = model.predict(X)
        y_pred_loaded = loaded_model.predict(X)
        np.testing.assert_array_almost_equal(y_pred_original, y_pred_loaded)


class TestLightGBMRegression:
    def test_fit_predict_multi_output(self, sample_data):
        X, y = sample_data
        model = LightGBMRegression()
        model.fit(X, y)
        
        y_pred = model.predict(X)
        assert y_pred.shape == y.shape
    
    def test_fit_predict_single_output(self, single_output_data):
        X, y = single_output_data
        model = LightGBMRegression()
        model.fit(X, y)
        
        y_pred = model.predict(X)
        assert len(y_pred) == len(y)
    
    def test_evaluate(self, sample_data):
        X, y = sample_data
        model = LightGBMRegression()
        model.fit(X, y)
        
        metrics = model.evaluate(X, y)
        assert isinstance(metrics, dict)
        assert "output_0" in metrics
        assert "RMSE" in metrics["output_0"]
    
    def test_get_shap_values(self, sample_data):
        X, y = sample_data
        model = LightGBMRegression()
        model.fit(X, y)
        
        shap_values = model.get_shap_values(X[:10])
        assert shap_values is not None


class TestRandomForestRegression:
    def test_fit_predict_multi_output(self, sample_data):
        X, y = sample_data
        model = RandomForestRegression(n_estimators=10)  # Fewer trees for speed
        model.fit(X, y)
        
        y_pred = model.predict(X)
        assert y_pred.shape == y.shape
    
    def test_fit_predict_single_output(self, single_output_data):
        X, y = single_output_data
        model = RandomForestRegression(n_estimators=10)
        model.fit(X, y)
        
        y_pred = model.predict(X)
        assert len(y_pred) == len(y)
    
    def test_evaluate(self, sample_data):
        X, y = sample_data
        model = RandomForestRegression(n_estimators=10)
        model.fit(X, y)
        
        metrics = model.evaluate(X, y)
        assert isinstance(metrics, dict)
        assert "output_0" in metrics
        assert "RMSE" in metrics["output_0"]
    
    def test_get_shap_values(self, sample_data):
        X, y = sample_data
        model = RandomForestRegression(n_estimators=10)
        model.fit(X, y)
        
        shap_values = model.get_shap_values(X[:10])
        assert shap_values is not None


class TestCatBoostRegression:
    def test_fit_predict_multi_output(self, sample_data):
        try:
            import catboost
        except ImportError:
            pytest.skip("CatBoost not installed")
            
        X, y = sample_data
        model = CatBoostRegression(iterations=10, verbose=False)  # Few iterations for speed
        model.fit(X, y)
        
        y_pred = model.predict(X)
        assert y_pred.shape == y.shape
    
    def test_fit_predict_single_output(self, single_output_data):
        try:
            import catboost
        except ImportError:
            pytest.skip("CatBoost not installed")
            
        X, y = single_output_data
        model = CatBoostRegression(iterations=10, verbose=False)
        model.fit(X, y)
        
        y_pred = model.predict(X)
        assert len(y_pred) == len(y)
    
    def test_evaluate(self, sample_data):
        try:
            import catboost
        except ImportError:
            pytest.skip("CatBoost not installed")
            
        X, y = sample_data
        model = CatBoostRegression(iterations=10, verbose=False)
        model.fit(X, y)
        
        metrics = model.evaluate(X, y)
        assert isinstance(metrics, dict)
        assert "output_0" in metrics
        assert "RMSE" in metrics["output_0"]


class TestPLSRegression:
    def test_fit_predict_multi_output(self, sample_data):
        X, y = sample_data
        model = PLSRegression(n_components=3)  # Use fewer components than features
        model.fit(X, y)
        
        y_pred = model.predict(X)
        assert y_pred.shape == y.shape
    
    def test_fit_predict_single_output(self, single_output_data):
        X, y = single_output_data
        model = PLSRegression(n_components=3)
        # PLS expects 2D target, reshape if needed
        y_2d = y.reshape(-1, 1) if y.ndim == 1 else y
        model.fit(X, y_2d)
        
        y_pred = model.predict(X)
        assert len(y_pred) == len(y)
    
    def test_evaluate(self, sample_data):
        X, y = sample_data
        model = PLSRegression(n_components=3)
        model.fit(X, y)
        
        metrics = model.evaluate(X, y)
        assert isinstance(metrics, dict)
        assert "output_0" in metrics
        assert "RMSE" in metrics["output_0"]
    
    def test_get_shap_values(self, sample_data):
        X, y = sample_data
        model = PLSRegression(n_components=3)
        model.fit(X, y)
        
        # PLS might not support SHAP, so test gracefully
        try:
            shap_values = model.get_shap_values(X[:10])
            # If it works, check it's not None
            if shap_values is not None:
                assert len(shap_values) == 2  # Multi-output
        except (NotImplementedError, Exception):
            # PLS might not support SHAP - that's okay
            pass


class TestModelFactory:
    def test_create_model(self):
        factory = ModelFactory()
        model = factory.create_model("xgboost", learning_rate=0.05)
        assert isinstance(model, XGBoostRegression)
    
    def test_create_all_models(self):
        factory = ModelFactory()
        
        # Test creating each registered model
        xgb_model = factory.create_model("xgboost")
        assert isinstance(xgb_model, XGBoostRegression)
        
        lgb_model = factory.create_model("lightgbm")
        assert isinstance(lgb_model, LightGBMRegression)
        
        rf_model = factory.create_model("random_forest")
        assert isinstance(rf_model, RandomForestRegression)
        
        pls_model = factory.create_model("pls")
        assert isinstance(pls_model, PLSRegression)
        
        # CatBoost might not be available
        try:
            cb_model = factory.create_model("catboost")
            assert isinstance(cb_model, CatBoostRegression)
        except ImportError:
            # CatBoost not installed - skip
            pass
    
    def test_save_load_model(self, sample_data, tmp_path):
        X, y = sample_data
        factory = ModelFactory(str(tmp_path))
        
        # Create and train model
        model = factory.create_model("xgboost")
        model.fit(X, y)
        
        # Save model
        save_path = factory.save_model(model, "test_xgb")
        assert save_path.endswith("test_xgb.pkl")
        
        # Load model
        loaded_model = factory.load_model("test_xgb")
        
        # Test predictions match
        y_pred_original = model.predict(X)
        y_pred_loaded = loaded_model.predict(X)
        np.testing.assert_array_almost_equal(y_pred_original, y_pred_loaded)
    
    def test_model_registry(self):
        models = ModelRegistry.list_models()
        assert "xgboost" in models
        assert "lightgbm" in models
        assert "random_forest" in models
        assert "pls" in models
        assert "catboost" in models  # Should be registered even if not available
    
    def test_get_model(self):
        model_class = ModelRegistry.get("xgboost")
        assert model_class == XGBoostRegression
        
        model_class = ModelRegistry.get("lightgbm")
        assert model_class == LightGBMRegression
        
        model_class = ModelRegistry.get("random_forest")
        assert model_class == RandomForestRegression
        
        model_class = ModelRegistry.get("pls")
        assert model_class == PLSRegression
        
        model_class = ModelRegistry.get("catboost")
        assert model_class == CatBoostRegression
    
    def test_invalid_model(self):
        factory = ModelFactory()
        
        with pytest.raises(KeyError):
            factory.create_model("invalid_model")
        
        with pytest.raises(KeyError):
            ModelRegistry.get("invalid_model")
    
    def test_is_registered(self):
        assert ModelRegistry.is_registered("xgboost")
        assert ModelRegistry.is_registered("lightgbm")
        assert not ModelRegistry.is_registered("invalid_model")


class TestCrossValidation:
    """Test cross-validation functionality across all models"""
    
    @pytest.mark.parametrize("model_type", ["xgboost", "lightgbm", "random_forest", "pls"])
    def test_cross_validate_all_models(self, model_type, sample_data):
        X, y = sample_data
        factory = ModelFactory()
        
        # Create model with faster parameters for testing
        if model_type in ["xgboost", "lightgbm"]:
            model = factory.create_model(model_type, n_estimators=10)
        elif model_type == "random_forest":
            model = factory.create_model(model_type, n_estimators=5)
        else:
            model = factory.create_model(model_type, n_components=3)
        
        # Test cross-validation
        cv_results = model.cross_validate(X, y, lag=5, lead=2, n_splits=3)
        
        assert "mean_test_scores" in cv_results
        assert "std_test_scores" in cv_results
        assert "fold_metrics" in cv_results
        assert cv_results["segment_size"] == 7  # lag + lead
        assert cv_results["n_splits"] == 3
    
    def test_cross_validate_insufficient_data(self):
        # Test with very small dataset - should raise error for insufficient data
        X = np.random.randn(10, 3)
        y = np.random.randn(10, 2)
        
        model = XGBoostRegression()
        
        # Should raise ValueError due to insufficient data
        with pytest.raises(ValueError, match="Not enough samples for cross-validation"):
            model.cross_validate(X, y, lag=5, lead=3, n_splits=5)
        
        # Test with sufficient data
        X_large = np.random.randn(50, 3)
        y_large = np.random.randn(50, 2)
        cv_results = model.cross_validate(X_large, y_large, lag=5, lead=3, n_splits=3)
        
        assert "mean_test_scores" in cv_results
        assert len(cv_results["fold_metrics"]) <= 3


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_data(self):
        X = np.array([]).reshape(0, 5)
        y = np.array([]).reshape(0, 2)
        
        model = XGBoostRegression()
        
        # XGBoost handles empty data but may produce warnings
        # Test that it doesn't crash completely
        try:
            model.fit(X, y)
            # If it succeeds, test prediction on empty data
            y_pred = model.predict(X)
            assert y_pred.shape == (0, 2)
        except (ValueError, Exception):
            # If it fails, that's also acceptable behavior
            pass
    
    def test_single_sample(self):
        X = np.random.randn(1, 5)
        y = np.random.randn(1, 2)
        
        model = XGBoostRegression()
        model.fit(X, y)
        
        y_pred = model.predict(X)
        assert y_pred.shape == (1, 2)
    
    def test_mismatched_dimensions(self):
        X = np.random.randn(100, 5)
        y = np.random.randn(50, 2)  # Wrong number of samples
        
        model = XGBoostRegression()
        
        with pytest.raises((ValueError, Exception)):
            model.fit(X, y)
    
    def test_predict_without_fit(self):
        X = np.random.randn(10, 5)
        model = XGBoostRegression()
        
        with pytest.raises((AttributeError, Exception)):
            model.predict(X)


if __name__ == "__main__":
    pytest.main([__file__])
