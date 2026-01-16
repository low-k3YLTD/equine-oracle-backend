"""
Model Registry with Version Management and Compatibility Layer
Handles model loading, versioning, and fallback strategies
"""

import os
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import joblib
import pickle
from packaging import version
import sklearn
import xgboost
import lightgbm

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Centralized model management with version compatibility and fallback handling.
    
    Features:
    - Version tracking and compatibility checking
    - Automatic fallback for incompatible models
    - Model loading with error handling
    - Model validation and interface checking
    - Version history management
    """
    
    def __init__(self, registry_path: str = "./models"):
        """
        Initialize model registry.
        
        Args:
            registry_path: Path to model storage directory
        """
        self.registry_path = registry_path
        self.models = {}
        self.version_manifest = {}
        self.loaded_models = {}
        self.compatibility_issues = []
        
        # Create registry directory if it doesn't exist
        os.makedirs(registry_path, exist_ok=True)
        
        # Load manifest if it exists
        manifest_path = os.path.join(registry_path, 'manifest.json')
        if os.path.exists(manifest_path):
            self._load_manifest(manifest_path)
        
        logger.info(f"Initialized ModelRegistry at {registry_path}")
    
    def _load_manifest(self, manifest_path: str) -> None:
        """Load version manifest from JSON."""
        try:
            with open(manifest_path, 'r') as f:
                self.version_manifest = json.load(f)
            logger.info(f"Loaded manifest with {len(self.version_manifest)} models")
        except Exception as e:
            logger.warning(f"Failed to load manifest: {str(e)}")
    
    def _save_manifest(self) -> None:
        """Save version manifest to JSON."""
        manifest_path = os.path.join(self.registry_path, 'manifest.json')
        try:
            with open(manifest_path, 'w') as f:
                json.dump(self.version_manifest, f, indent=2)
            logger.info("Saved manifest")
        except Exception as e:
            logger.error(f"Failed to save manifest: {str(e)}")
    
    def _is_compatible(self, required_version: str, current_version: str) -> bool:
        """
        Check if current version is compatible with required version.
        
        Args:
            required_version: Required version string
            current_version: Current version string
        
        Returns:
            True if compatible, False otherwise
        """
        try:
            # Allow patch version differences
            req_major_minor = '.'.join(required_version.split('.')[:2])
            curr_major_minor = '.'.join(current_version.split('.')[:2])
            return req_major_minor == curr_major_minor
        except Exception as e:
            logger.warning(f"Version comparison failed: {str(e)}")
            return False
    
    def _validate_model_interface(self, model: Any) -> bool:
        """
        Validate that model has required interface.
        
        Args:
            model: Model to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_methods = ['predict', 'predict_proba']
        for method in required_methods:
            if not hasattr(model, method):
                logger.warning(f"Model missing method: {method}")
                return False
        return True
    
    def register_model(
        self,
        model_name: str,
        model: Any,
        version: str,
        sklearn_version: Optional[str] = None,
        xgboost_version: Optional[str] = None,
        lightgbm_version: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Register a model with version information.
        
        Args:
            model_name: Name of the model
            model: Model object
            version: Model version
            sklearn_version: Required sklearn version
            xgboost_version: Required xgboost version
            lightgbm_version: Required lightgbm version
            metadata: Additional metadata
        """
        self.version_manifest[model_name] = {
            'version': version,
            'sklearn_version': sklearn_version or sklearn.__version__,
            'xgboost_version': xgboost_version or xgboost.__version__,
            'lightgbm_version': lightgbm_version or lightgbm.__version__,
            'registered_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        # Save model
        model_path = os.path.join(self.registry_path, f"{model_name}_{version}.pkl")
        try:
            joblib.dump(model, model_path)
            logger.info(f"Registered model {model_name} v{version}")
        except Exception as e:
            logger.error(f"Failed to save model {model_name}: {str(e)}")
        
        self._save_manifest()
    
    def load_model_safe(self, model_name: str, model_version: Optional[str] = None) -> Optional[Any]:
        """
        Load model with version validation and fallback.
        
        Args:
            model_name: Name of the model to load
            model_version: Specific version to load (latest if None)
        
        Returns:
            Loaded model or None if loading failed
        """
        try:
            # Get model info from manifest
            if model_name not in self.version_manifest:
                logger.error(f"Model {model_name} not found in registry")
                return None
            
            manifest_entry = self.version_manifest[model_name]
            required_version = manifest_entry.get('sklearn_version')
            current_version = sklearn.__version__
            
            # Check compatibility
            if not self._is_compatible(required_version, current_version):
                logger.warning(
                    f"Version mismatch for {model_name}: "
                    f"requires sklearn {required_version}, have {current_version}"
                )
                self.compatibility_issues.append({
                    'model': model_name,
                    'required': required_version,
                    'current': current_version,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Try legacy loading
                return self._load_legacy_model(model_name, manifest_entry)
            
            # Load model
            version_to_load = model_version or manifest_entry['version']
            model_path = os.path.join(
                self.registry_path,
                f"{model_name}_{version_to_load}.pkl"
            )
            
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return None
            
            model = joblib.load(model_path)
            
            # Validate interface
            if not self._validate_model_interface(model):
                logger.error(f"Model {model_name} has invalid interface")
                return None
            
            self.loaded_models[model_name] = {
                'model': model,
                'version': version_to_load,
                'loaded_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Successfully loaded {model_name} v{version_to_load}")
            return model
            
        except Exception as e:
            logger.error(f"Error loading {model_name}: {str(e)}")
            return None
    
    def _load_legacy_model(self, model_name: str, manifest_entry: Dict) -> Optional[Any]:
        """
        Load older models using compatibility layer.
        
        Args:
            model_name: Name of the model
            manifest_entry: Manifest entry for the model
        
        Returns:
            Loaded model or None
        """
        logger.info(f"Attempting legacy loading for {model_name}")
        
        try:
            # Try with different pickle protocols
            model_path = os.path.join(
                self.registry_path,
                f"{model_name}_{manifest_entry['version']}.pkl"
            )
            
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return None
            
            # Try different loading strategies
            try:
                # Strategy 1: Standard joblib load
                model = joblib.load(model_path)
                logger.info(f"Legacy load successful for {model_name} (strategy 1)")
                return model
            except Exception:
                # Strategy 2: Use pickle with different protocol
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                logger.info(f"Legacy load successful for {model_name} (strategy 2)")
                return model
                
        except Exception as e:
            logger.error(f"Legacy loading failed for {model_name}: {str(e)}")
            return None
    
    def _fallback_model(self, model_name: str) -> None:
        """
        Handle fallback when model can't be loaded.
        
        Args:
            model_name: Name of the model that failed
        """
        logger.warning(f"Ensemble will run without {model_name}")
    
    def load_ensemble(self, model_names: list) -> Dict[str, Any]:
        """
        Load multiple models for ensemble.
        
        Args:
            model_names: List of model names to load
        
        Returns:
            Dictionary of successfully loaded models
        """
        ensemble = {}
        
        for model_name in model_names:
            model = self.load_model_safe(model_name)
            if model is not None:
                ensemble[model_name] = model
            else:
                self._fallback_model(model_name)
        
        logger.info(f"Loaded ensemble with {len(ensemble)}/{len(model_names)} models")
        return ensemble
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """
        Get information about a registered model.
        
        Args:
            model_name: Name of the model
        
        Returns:
            Model information or None
        """
        return self.version_manifest.get(model_name)
    
    def list_models(self) -> Dict[str, Dict]:
        """
        List all registered models.
        
        Returns:
            Dictionary of all registered models
        """
        return self.version_manifest
    
    def get_compatibility_report(self) -> Dict:
        """
        Get report of compatibility issues.
        
        Returns:
            Dictionary with compatibility information
        """
        return {
            'total_issues': len(self.compatibility_issues),
            'issues': self.compatibility_issues,
            'loaded_models': list(self.loaded_models.keys()),
            'manifest_models': list(self.version_manifest.keys())
        }
    
    def get_status(self) -> Dict:
        """Get registry status."""
        return {
            'registry_path': self.registry_path,
            'total_models': len(self.version_manifest),
            'loaded_models': len(self.loaded_models),
            'compatibility_issues': len(self.compatibility_issues),
            'models': self.version_manifest,
            'loaded': self.loaded_models
        }


class CompatibilityLayer:
    """
    Compatibility layer for handling different versions of dependencies.
    """
    
    @staticmethod
    def get_sklearn_version() -> str:
        """Get sklearn version."""
        return sklearn.__version__
    
    @staticmethod
    def get_xgboost_version() -> str:
        """Get xgboost version."""
        return xgboost.__version__
    
    @staticmethod
    def get_lightgbm_version() -> str:
        """Get lightgbm version."""
        return lightgbm.__version__
    
    @staticmethod
    def check_dependencies() -> Dict[str, bool]:
        """
        Check if all required dependencies are available.
        
        Returns:
            Dictionary of dependency status
        """
        dependencies = {
            'sklearn': True,
            'xgboost': True,
            'lightgbm': True,
            'numpy': True,
            'pandas': True
        }
        
        try:
            import numpy
        except ImportError:
            dependencies['numpy'] = False
        
        try:
            import pandas
        except ImportError:
            dependencies['pandas'] = False
        
        return dependencies
    
    @staticmethod
    def validate_environment() -> bool:
        """
        Validate that the environment has all required dependencies.
        
        Returns:
            True if environment is valid
        """
        deps = CompatibilityLayer.check_dependencies()
        missing = [k for k, v in deps.items() if not v]
        
        if missing:
            logger.error(f"Missing dependencies: {missing}")
            return False
        
        logger.info("Environment validation successful")
        return True
