import pandas as pd
import numpy as np
import joblib
import os
import logging
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMRanker

# --- Configuration ---
TARGET_COL = 'relevance_score'
GROUP_COL = 'race_id'
DATA_PATH = "/home/ubuntu/racebase_processed_final_large.csv" # New large data
ENSEMBLE_MODEL_PATH = '/home/ubuntu/ensemble_ranking_model_large.pkl'

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data_for_ensemble(data_path):
    """Loads and prepares data for ensemble prediction."""
    logger.info("Loading data for ensemble...")
    try:
        # The new data has a header and the correct columns
        df = pd.read_csv(data_path)
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}. Exiting.")
        raise
    
    # Features: Exclude target and group columns
    all_feature_cols = [col for col in df.columns if col not in [TARGET_COL, GROUP_COL]]
    
    # Load the feature columns used by the pre-trained models (if available)
    try:
        base_model_feature_cols = joblib.load('/home/ubuntu/feature_columns.pkl')
    except Exception as e:
        logger.warning(f"Could not load base model feature columns: {e}. Using a subset of the first 12 features as a proxy.")
        # Fallback to the first 12 features as a proxy for the base models
        base_model_feature_cols = df.columns[:12].tolist()
        
    # The new LightGBM Ranker was trained on all features, but the base models were trained on a subset.
    X_full = df[all_feature_cols]
    
    # Create the subset X for base models
    # We must ensure that the columns in X_full are a superset of base_model_feature_cols
    try:
        X_base = X_full[base_model_feature_cols]
    except KeyError as e:
        logger.warning(f"Feature mismatch for base models: {e}. Falling back to a subset of features.")
        # Use the first N columns as the base features, where N is the number of features in the base model
        X_base = X_full.iloc[:, :len(base_model_feature_cols)]
        X_base.columns = base_model_feature_cols # Rename to match the scaler's expected input
        
    logger.info(f"X_full shape: {X_full.shape}, X_base shape: {X_base.shape}")
        
    return df, X_full, X_base, all_feature_cols

def load_base_models(model_dir='/home/ubuntu/'):
    """Loads all base models for the ensemble."""
    models = {}
    
    # Load the newly trained LightGBM Ranker (from the large dataset)
    try:
        models['lgbm_ranker'] = joblib.load(os.path.join(model_dir, 'lightgbm_ranker_large.pkl'))
        logger.info("Loaded new LightGBM Ranker (large data).")
    except FileNotFoundError:
        logger.warning("New LightGBM Ranker (large data) not found. Skipping.")

    # Load pre-trained classification models (assuming they are for binary classification)
    model_files = {
        'logistic_regression': 'logistic_regression_model.pkl',
        'random_forest': 'random_forest_model.pkl',
        'gradient_boosting': 'gradient_boosting_model.pkl',
        'xgboost': 'xgboost_model.pkl',
        'lightgbm_old': 'lightgbm_model.pkl' # The old LightGBM model
    }
    
    for name, filename in model_files.items():
        try:
            models[name] = joblib.load(os.path.join(model_dir, filename))
            logger.info(f"Loaded pre-trained model: {name}")
        except Exception as e:
            logger.warning(f"Could not load pre-trained model {name} from {filename}: {e}. Skipping.")
        
    # Load scaler
    try:
        scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
        models['scaler'] = scaler
        logger.info("Loaded scaler.")
    except FileNotFoundError:
        logger.warning("Scaler not found. Skipping scaling for LR model.")
        
    return models

def create_ensemble_predictions(df, X_full, X_base, models):
    """Generates predictions from all base models and combines them."""
    
    # Scale data for LR model if scaler is available
    X_base_scaled = X_base.copy()
    if 'scaler' in models:
        try:
            X_base_scaled = models['scaler'].transform(X_base)
            logger.info("Base data scaled for Logistic Regression model.")
        except Exception as e:
            logger.warning(f"Scaling failed: {e}. Using unscaled data for LR.")
            X_base_scaled = X_base
    
    # --- 1. Generate Base Predictions (Scores) ---
    predictions = pd.DataFrame(index=X_full.index)
    
    # New LightGBM Ranker (uses full features)
    if 'lgbm_ranker' in models:
        try:
            predictions['lgbm_ranker_score'] = models['lgbm_ranker'].predict(X_full)
            logger.info("Generated predictions from New LightGBM Ranker (full features).")
        except Exception as e:
            logger.warning(f"Prediction failed for new LightGBM Ranker due to error: {e}. Skipping this model.")
        
    # Classification Models (predict_proba for ranking score)
    for name in ['logistic_regression', 'random_forest', 'gradient_boosting', 'xgboost', 'lightgbm_old']:
        if name in models:
            # Use scaled base data for LR, raw base data for tree-based models
            data = X_base_scaled if name == 'logistic_regression' and 'scaler' in models else X_base
            
            # Check if the model has predict_proba
            if hasattr(models[name], 'predict_proba'):
                try:
                    predictions[f'{name}_score'] = models[name].predict_proba(data)[:, 1]
                    logger.info(f"Generated probability scores from {name} (base features).")
                except Exception as e:
                    logger.warning(f"Prediction failed for model {name} due to error: {e}. Skipping this model.")
            else:
                logger.warning(f"Model {name} does not have predict_proba. Skipping.")

    # --- 2. Ensemble Strategy: Simple Averaging ---
    score_cols = [col for col in predictions.columns if '_score' in col]
    
    if not score_cols:
        logger.error("No base model scores were generated. Cannot create ensemble.")
        return None
        
    predictions['ensemble_score'] = predictions[score_cols].mean(axis=1)
    logger.info(f"Created ensemble score by averaging {len(score_cols)} base model scores.")
    
    # --- 3. Final Ranking ---
    df['ensemble_score'] = predictions['ensemble_score']
    
    # Group by race and rank the horses based on the ensemble score
    df['ensemble_rank'] = df.groupby(GROUP_COL)['ensemble_score'].rank(method='first', ascending=False)
    
    return df

def run_ensemble_system():
    """Main function to run the ensemble system."""
    logger.info("Starting Ensemble Prediction System (Large Data)...")
    
    try:
        df, X_full, X_base, all_feature_cols = load_data_for_ensemble(DATA_PATH)
        logger.info("Data loading complete.")
    except Exception as e:
        logger.error(f"Error during data loading: {e}")
        return
        
    models = load_base_models()
    
    if not models:
        logger.error("No models loaded. Exiting ensemble system.")
        return
        
    df_ranked = create_ensemble_predictions(df, X_full, X_base, models)
    
    if df_ranked is None:
        return
        
    # --- Save Ensemble Results (for demonstration/testing) ---
    df_ranked.to_csv('/home/ubuntu/ensemble_predictions_large.csv', index=False)
    logger.info("Ensemble predictions saved to /home/ubuntu/ensemble_predictions_large.csv")
    
    logger.info("Ensemble system execution complete.")

if __name__ == "__main__":
    # Ensure all required libraries are installed
    try:
        import lightgbm
        import sklearn
    except ImportError:
        logger.error("Required libraries (lightgbm, scikit-learn) are not installed. Please install them.")
        exit(1)
        
    run_ensemble_system()
