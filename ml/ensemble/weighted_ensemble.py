"""
Weighted Ensemble for Horse Race Predictions
Implements performance-based model weighting with confidence adjustment
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
from datetime import datetime
import joblib

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Performance metrics for a model"""
    name: str
    ndcg_at_1: float
    ndcg_at_3: float
    precision: float
    recall: float
    f1_score: float
    calibration_error: float
    confidence_score: float


class WeightedEnsemble:
    """
    Weighted ensemble combining multiple ML models with confidence-based weighting.
    
    Features:
    - Performance-based weight optimization
    - Confidence adjustment for predictions
    - Model-specific calibration
    - Dynamic weight updates
    - Version tracking
    """
    
    def __init__(self, models: Dict[str, any], version: str = "1.0"):
        """
        Initialize weighted ensemble.
        
        Args:
            models: Dictionary of model_name -> model_instance
            version: Version identifier for tracking
        """
        self.models = models
        self.version = version
        self.weights = {}
        self.calibrators = {}
        self.model_metrics = {}
        self.created_at = datetime.utcnow()
        self.prediction_count = 0
        
        logger.info(f"Initialized WeightedEnsemble v{version} with {len(models)} models")
    
    def set_weights(self, weights: Dict[str, float]) -> None:
        """
        Set model weights manually or from optimization.
        
        Args:
            weights: Dictionary of model_name -> weight (should sum to 1.0)
        
        Raises:
            ValueError: If weights don't sum to 1.0 or contain invalid models
        """
        # Validate weights
        total_weight = sum(weights.values())
        if not np.isclose(total_weight, 1.0, atol=0.01):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
        
        invalid_models = set(weights.keys()) - set(self.models.keys())
        if invalid_models:
            raise ValueError(f"Invalid models in weights: {invalid_models}")
        
        self.weights = weights
        logger.info(f"Set weights: {weights}")
    
    def set_model_metrics(self, metrics: Dict[str, ModelMetrics]) -> None:
        """
        Set performance metrics for models.
        
        Args:
            metrics: Dictionary of model_name -> ModelMetrics
        """
        self.model_metrics = metrics
        logger.info(f"Updated metrics for {len(metrics)} models")
    
    def fit_calibration(self, X_val: np.ndarray, y_val: np.ndarray) -> None:
        """
        Fit probability calibration for each model.
        
        Args:
            X_val: Validation features
            y_val: Validation targets
        """
        from sklearn.calibration import CalibratedClassifierCV
        
        for model_name, model in self.models.items():
            try:
                # Apply isotonic regression calibration
                calibrator = CalibratedClassifierCV(
                    model,
                    method='isotonic',
                    cv='prefit'
                )
                calibrator.fit(X_val, y_val)
                self.calibrators[model_name] = calibrator
                logger.info(f"Calibrated {model_name}")
            except Exception as e:
                logger.warning(f"Failed to calibrate {model_name}: {str(e)}")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using weighted ensemble.
        
        Args:
            X: Features array
        
        Returns:
            Ensemble predictions
        """
        if not self.weights:
            # Default equal weights if not set
            n_models = len(self.models)
            self.weights = {name: 1.0 / n_models for name in self.models.keys()}
        
        predictions = []
        weights_list = []
        
        for model_name, model in self.models.items():
            try:
                # Get model predictions
                if hasattr(model, 'predict_proba'):
                    probs = model.predict_proba(X)[:, 1]
                else:
                    probs = model.predict(X)
                
                predictions.append(probs)
                
                # Apply weight
                weight = self.weights.get(model_name, 1.0 / len(self.models))
                weights_list.append(weight)
                
            except Exception as e:
                logger.error(f"Error predicting with {model_name}: {str(e)}")
                # Skip this model
                continue
        
        if not predictions:
            raise RuntimeError("No models produced valid predictions")
        
        # Normalize weights for active models
        weights_array = np.array(weights_list)
        weights_array = weights_array / weights_array.sum()
        
        # Weighted average
        ensemble_pred = np.average(predictions, axis=0, weights=weights_array)
        
        self.prediction_count += len(X)
        return ensemble_pred
    
    def predict_with_confidence(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions with confidence scores.
        
        Args:
            X: Features array
        
        Returns:
            Tuple of (predictions, confidences)
        """
        if not self.weights:
            n_models = len(self.models)
            self.weights = {name: 1.0 / n_models for name in self.models.keys()}
        
        predictions = []
        confidences = []
        weights_list = []
        
        for model_name, model in self.models.items():
            try:
                # Get predictions
                if hasattr(model, 'predict_proba'):
                    probs = model.predict_proba(X)[:, 1]
                else:
                    probs = model.predict(X)
                
                predictions.append(probs)
                
                # Calculate confidence (distance from 0.5 threshold)
                confidence = np.mean(np.abs(probs - 0.5) * 2)
                confidences.append(confidence)
                
                # Apply weight
                weight = self.weights.get(model_name, 1.0 / len(self.models))
                weights_list.append(weight)
                
            except Exception as e:
                logger.error(f"Error predicting with {model_name}: {str(e)}")
                continue
        
        if not predictions:
            raise RuntimeError("No models produced valid predictions")
        
        # Normalize weights
        weights_array = np.array(weights_list)
        weights_array = weights_array / weights_array.sum()
        
        # Weighted average with confidence adjustment
        ensemble_pred = np.average(predictions, axis=0, weights=weights_array)
        ensemble_confidence = np.average(confidences, weights=weights_array)
        
        self.prediction_count += len(X)
        return ensemble_pred, ensemble_confidence
    
    def predict_with_uncertainty(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Make predictions with uncertainty intervals.
        
        Args:
            X: Features array
        
        Returns:
            Tuple of (predictions, lower_bound, upper_bound)
        """
        predictions = []
        
        for model_name, model in self.models.items():
            try:
                if hasattr(model, 'predict_proba'):
                    probs = model.predict_proba(X)[:, 1]
                else:
                    probs = model.predict(X)
                predictions.append(probs)
            except Exception as e:
                logger.error(f"Error predicting with {model_name}: {str(e)}")
                continue
        
        if not predictions:
            raise RuntimeError("No models produced valid predictions")
        
        predictions_array = np.array(predictions)
        
        # Calculate statistics
        mean_pred = np.mean(predictions_array, axis=0)
        std_pred = np.std(predictions_array, axis=0)
        
        # 95% confidence interval
        lower_bound = mean_pred - 1.96 * std_pred
        upper_bound = mean_pred + 1.96 * std_pred
        
        # Clip to [0, 1]
        lower_bound = np.clip(lower_bound, 0, 1)
        upper_bound = np.clip(upper_bound, 0, 1)
        
        return mean_pred, lower_bound, upper_bound
    
    def get_model_contributions(self, X: np.ndarray) -> pd.DataFrame:
        """
        Get contribution of each model to ensemble prediction.
        
        Args:
            X: Features array
        
        Returns:
            DataFrame with model contributions
        """
        contributions = {}
        
        for model_name, model in self.models.items():
            try:
                if hasattr(model, 'predict_proba'):
                    probs = model.predict_proba(X)[:, 1]
                else:
                    probs = model.predict(X)
                
                weight = self.weights.get(model_name, 1.0 / len(self.models))
                contributions[model_name] = probs * weight
                
            except Exception as e:
                logger.error(f"Error getting contribution from {model_name}: {str(e)}")
        
        return pd.DataFrame(contributions)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray, groups: Optional[np.ndarray] = None) -> Dict:
        """
        Evaluate ensemble performance.
        
        Args:
            X: Features array
            y: Target array
            groups: Group indices for ranking metrics (optional)
        
        Returns:
            Dictionary of evaluation metrics
        """
        from sklearn.metrics import ndcg_score, precision_score, recall_score, f1_score
        
        predictions = self.predict(X)
        
        metrics = {
            'ndcg_at_1': ndcg_score(y.reshape(1, -1), predictions.reshape(1, -1), k=1),
            'ndcg_at_3': ndcg_score(y.reshape(1, -1), predictions.reshape(1, -1), k=3),
            'precision': precision_score(y, (predictions > 0.5).astype(int)),
            'recall': recall_score(y, (predictions > 0.5).astype(int)),
            'f1': f1_score(y, (predictions > 0.5).astype(int)),
        }
        
        return metrics
    
    def save(self, path: str) -> None:
        """
        Save ensemble to disk.
        
        Args:
            path: File path to save to
        """
        joblib.dump(self, path)
        logger.info(f"Saved ensemble to {path}")
    
    @staticmethod
    def load(path: str) -> 'WeightedEnsemble':
        """
        Load ensemble from disk.
        
        Args:
            path: File path to load from
        
        Returns:
            Loaded ensemble
        """
        ensemble = joblib.load(path)
        logger.info(f"Loaded ensemble from {path}")
        return ensemble
    
    def get_status(self) -> Dict:
        """Get ensemble status."""
        return {
            'version': self.version,
            'models': list(self.models.keys()),
            'weights': self.weights,
            'prediction_count': self.prediction_count,
            'created_at': self.created_at.isoformat(),
            'calibrated_models': list(self.calibrators.keys()),
        }


class EnsembleOptimizer:
    """
    Optimize ensemble weights using Bayesian optimization.
    """
    
    def __init__(self, ensemble: WeightedEnsemble):
        """Initialize optimizer."""
        self.ensemble = ensemble
        self.optimization_history = []
    
    def optimize_weights(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        metric: str = 'ndcg_at_1',
        n_iterations: int = 100
    ) -> Dict[str, float]:
        """
        Optimize ensemble weights using Bayesian optimization.
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            metric: Metric to optimize ('ndcg_at_1', 'f1', etc.)
            n_iterations: Number of optimization iterations
        
        Returns:
            Optimized weights dictionary
        """
        from scipy.optimize import minimize
        from sklearn.metrics import ndcg_score
        
        def objective(weights_array):
            """Objective function to minimize (negative metric)."""
            # Normalize weights
            weights_norm = weights_array / weights_array.sum()
            
            # Set weights
            weight_dict = {
                name: w for name, w in zip(self.ensemble.models.keys(), weights_norm)
            }
            self.ensemble.set_weights(weight_dict)
            
            # Evaluate
            predictions = self.ensemble.predict(X_val)
            score = ndcg_score(y_val.reshape(1, -1), predictions.reshape(1, -1), k=1)
            
            return -score  # Minimize negative score
        
        # Initial weights (equal)
        n_models = len(self.ensemble.models)
        initial_weights = np.ones(n_models) / n_models
        
        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method='Nelder-Mead',
            options={'maxiter': n_iterations}
        )
        
        # Extract optimized weights
        optimized_weights_array = result.x / result.x.sum()
        optimized_weights = {
            name: w for name, w in zip(self.ensemble.models.keys(), optimized_weights_array)
        }
        
        logger.info(f"Optimized weights: {optimized_weights}")
        self.ensemble.set_weights(optimized_weights)
        
        return optimized_weights
