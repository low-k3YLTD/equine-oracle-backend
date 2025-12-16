import joblib
import os
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Define the directory where the models are expected
MODEL_DIR = "/home/ubuntu/"

# Ensure the directory exists (it should, but for safety)
os.makedirs(MODEL_DIR, exist_ok=True)

# --- 1. Mock Feature Columns ---
# These are the features the base models were trained on (a subset of the full features)
mock_base_features = [
    "distance", "distance_numeric", "year", "month", "day", "day_of_week",
    "week_of_year", "days_since_last_race", "PREV_RACE_WON", "WIN_STREAK",
    "IMPLIED_PROBABILITY", "NORMALIZED_VOLUME"
]
joblib.dump(mock_base_features, os.path.join(MODEL_DIR, 'feature_columns.pkl'))
print(f"Created mock feature_columns.pkl with {len(mock_base_features)} features.")

# --- 2. Mock Scaler ---
# Create a dummy scaler object
mock_scaler = StandardScaler()
# Fit it with dummy data to make it a valid object
dummy_data = np.array([
    [1000, 1000, 2020, 1, 1, 1, 1, 1, 0, 0, 0.5, 0.5],
    [1200, 1200, 2021, 2, 2, 2, 2, 2, 1, 1, 0.6, 0.6]
])
mock_scaler.fit(dummy_data)
joblib.dump(mock_scaler, os.path.join(MODEL_DIR, 'scaler.pkl'))
print("Created mock scaler.pkl.")

# --- 3. Mock Models ---
# Create a dummy Logistic Regression model (needs a predict_proba method)
mock_lr = LogisticRegression()
# Fit it with dummy data to make it a valid object
mock_lr.fit(dummy_data, np.array([0, 1]))
joblib.dump(mock_lr, os.path.join(MODEL_DIR, 'logistic_regression_model.pkl'))
print("Created mock logistic_regression_model.pkl.")

# Create a simple class to mock a model with a predict_proba method
class MockModel:
    def predict_proba(self, X):
        # Return a random probability array for each sample
        n_samples = X.shape[0]
        # Simulate a prediction: 50% chance of 0, 50% chance of 1
        probs = np.random.rand(n_samples) * 0.2 + 0.4 # Range 0.4 to 0.6
        return np.column_stack([1 - probs, probs])
    
    def predict(self, X):
        # Mock for the ranker
        n_samples = X.shape[0]
        return np.random.rand(n_samples) # Return a ranking score

# List of model files to mock
mock_model_files = [
    'lightgbm_ranker_large.pkl',
    'random_forest_model.pkl',
    'gradient_boosting_model.pkl',
    'xgboost_model.pkl',
    'lightgbm_model.pkl'
]

for filename in mock_model_files:
    # Use the MockModel class for all others
    model_to_dump = MockModel()
    joblib.dump(model_to_dump, os.path.join(MODEL_DIR, filename))
    print(f"Created mock {filename}.")

print("\nMock model creation complete.")
