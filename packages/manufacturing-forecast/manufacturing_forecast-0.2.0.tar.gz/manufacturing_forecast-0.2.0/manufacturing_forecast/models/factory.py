"""
Model factory and registry for dynamic model creation and management.
"""
import os
import joblib
import logging
from typing import Dict, Type, Optional, Any, List
from pathlib import Path

from .base import BaseRegression

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for available model types"""
    
    _models: Dict[str, Type[BaseRegression]] = {}
    
    @classmethod
    def register(cls, name: str, model_class: Type[BaseRegression]) -> None:
        """
        Register a model class with the registry.
        
        Args:
            name: Name identifier for the model
            model_class: Model class that inherits from BaseRegression
        """
        if not issubclass(model_class, BaseRegression):
            raise ValueError(f"{model_class} must inherit from BaseRegression")
        
        cls._models[name.lower()] = model_class
        logger.info(f"Registered model: {name}")
    
    @classmethod
    def get(cls, name: str) -> Type[BaseRegression]:
        """
        Get a model class from the registry.
        
        Args:
            name: Name of the model
            
        Returns:
            Model class
            
        Raises:
            KeyError: If model is not registered
        """
        if name.lower() not in cls._models:
            available = ", ".join(cls._models.keys())
            raise KeyError(f"Model '{name}' not found. Available models: {available}")
        
        return cls._models[name.lower()]
    
    @classmethod
    def list_models(cls) -> List[str]:
        """Get list of registered model names"""
        return list(cls._models.keys())
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a model is registered"""
        return name.lower() in cls._models


class ModelFactory:
    """Factory for creating and managing ML models"""
    
    def __init__(self, model_path: str = "/models"):
        """
        Initialize the model factory.
        
        Args:
            model_path: Path to directory containing saved models
        """
        self.model_path = Path(model_path)
        self.loaded_models: Dict[str, BaseRegression] = {}
        
        # Ensure model directory exists
        self.model_path.mkdir(parents=True, exist_ok=True)
    
    def create_model(self, model_type: str, **kwargs) -> BaseRegression:
        """
        Create a new model instance.
        
        Args:
            model_type: Type of model to create
            **kwargs: Additional parameters for model initialization
            
        Returns:
            New model instance
        """
        model_class = ModelRegistry.get(model_type)
        return model_class(**kwargs)
    
    def load_model(self, model_id: str, filepath: Optional[str] = None) -> BaseRegression:
        """
        Load a model from disk.
        
        Args:
            model_id: Identifier for the model
            filepath: Optional custom filepath, otherwise uses model_path/model_id
            
        Returns:
            Loaded model instance
        """
        if model_id in self.loaded_models:
            logger.info(f"Returning cached model: {model_id}")
            return self.loaded_models[model_id]
        
        if filepath is None:
            filepath = self.model_path / model_id
            if not filepath.suffix:
                filepath = filepath.with_suffix('.pkl')
        else:
            filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        try:
            model = joblib.load(filepath)
            self.loaded_models[model_id] = model
            logger.info(f"Loaded model from {filepath}")
            return model
        except Exception as e:
            logger.error(f"Error loading model from {filepath}: {e}")
            raise
    
    def save_model(self, model: BaseRegression, model_id: str, filepath: Optional[str] = None) -> str:
        """
        Save a model to disk.
        
        Args:
            model: Model instance to save
            model_id: Identifier for the model
            filepath: Optional custom filepath, otherwise uses model_path/model_id.pkl
            
        Returns:
            Path where model was saved
        """
        if filepath is None:
            filepath = self.model_path / f"{model_id}.pkl"
        else:
            filepath = Path(filepath)
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            joblib.dump(model, filepath)
            self.loaded_models[model_id] = model
            logger.info(f"Saved model to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving model to {filepath}: {e}")
            raise
    
    def load_all_models(self, model_files: List[str]) -> Dict[str, BaseRegression]:
        """
        Load multiple models from disk.
        
        Args:
            model_files: List of model filenames to load
            
        Returns:
            Dictionary of loaded models
        """
        models = {}
        for model_file in model_files:
            try:
                model_id = Path(model_file).stem
                model = self.load_model(model_id, self.model_path / model_file)
                models[model_id] = model
            except Exception as e:
                logger.error(f"Failed to load model {model_file}: {e}")
        
        return models
    
    def get_loaded_models(self) -> Dict[str, BaseRegression]:
        """Get all currently loaded models"""
        return self.loaded_models.copy()
    
    def clear_cache(self) -> None:
        """Clear the loaded models cache"""
        self.loaded_models.clear()
        logger.info("Cleared model cache")