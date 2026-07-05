-- Equine Oracle ML Training Database Schema
-- MySQL/MariaDB compatible

CREATE DATABASE IF NOT EXISTS equine_oracle_training
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE equine_oracle_training;

-- Race information
CREATE TABLE IF NOT EXISTS races (
  id INT AUTO_INCREMENT PRIMARY KEY,
  race_id VARCHAR(50) NOT NULL UNIQUE,
  track VARCHAR(100) NOT NULL,
  race_date DATE NOT NULL,
  race_type VARCHAR(50) NOT NULL,
  distance INT NOT NULL,
  surface VARCHAR(20) NOT NULL,
  weather VARCHAR(50),
  track_condition VARCHAR(50),
  prize_money DECIMAL(12,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  INDEX idx_race_date (race_date),
  INDEX idx_track (track),
  INDEX idx_race_type (race_type)
) ENGINE=InnoDB;

-- Horse information
CREATE TABLE IF NOT EXISTS horses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  horse_id VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  sire VARCHAR(100),
  dam VARCHAR(100),
  foaling_date DATE,
  sex VARCHAR(10),
  color VARCHAR(20),
  country VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  INDEX idx_horse_name (name)
) ENGINE=InnoDB;

-- Race participants (horse-race mapping)
CREATE TABLE IF NOT EXISTS race_participants (
  id INT AUTO_INCREMENT PRIMARY KEY,
  race_id INT NOT NULL,
  horse_id INT NOT NULL,
  jockey VARCHAR(100),
  trainer VARCHAR(100),
  barrier INT,
  weight DECIMAL(6,2),
  odds DECIMAL(8,2),
  finishing_position INT,
  margin DECIMAL(6,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,
  FOREIGN KEY (horse_id) REFERENCES horses(id) ON DELETE CASCADE,
  
  INDEX idx_race_participant (race_id, horse_id),
  INDEX idx_finishing_position (finishing_position)
) ENGINE=InnoDB;

-- Historical performance data
CREATE TABLE IF NOT EXISTS horse_performances (
  id INT AUTO_INCREMENT PRIMARY KEY,
  horse_id INT NOT NULL,
  race_id INT NOT NULL,
  race_date DATE NOT NULL,
  finishing_position INT,
  margin DECIMAL(6,2),
  odds DECIMAL(8,2),
  weight DECIMAL(6,2),
  barrier INT,
  jockey VARCHAR(100),
  trainer VARCHAR(100),
  track VARCHAR(100),
  distance INT,
  surface VARCHAR(20),
  race_type VARCHAR(50),
  prize_money DECIMAL(12,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (horse_id) REFERENCES horses(id) ON DELETE CASCADE,
  FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,
  
  INDEX idx_horse_performance (horse_id, race_date),
  INDEX idx_race_performance (race_id)
) ENGINE=InnoDB;

-- Training data for ML models
CREATE TABLE IF NOT EXISTS training_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  race_id VARCHAR(50) NOT NULL,
  horse_id VARCHAR(50) NOT NULL,
  
  -- Race features
  distance INT,
  race_type VARCHAR(50),
  track VARCHAR(100),
  surface VARCHAR(20),
  
  -- Horse features
  horse_age INT,
  horse_sex VARCHAR(10),
  horse_country VARCHAR(50),
  
  -- Performance features
  days_since_last_race INT,
  avg_finishing_position_5 DECIMAL(4,2),
  avg_finishing_position_10 DECIMAL(4,2),
  win_rate_5 DECIMAL(5,4),
  win_rate_10 DECIMAL(5,4),
  place_rate_5 DECIMAL(5,4),
  place_rate_10 DECIMAL(5,4),
  
  -- Jockey/Trainer features
  jockey_win_rate DECIMAL(5,4),
  trainer_win_rate DECIMAL(5,4),
  
  -- Market features
  odds DECIMAL(8,2),
  implied_probability DECIMAL(5,4),
  
  -- Target variable
  result INT NOT NULL,  -- 1 = win, 0 = lose
  finishing_position INT,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_training_race (race_id),
  INDEX idx_training_horse (horse_id),
  INDEX idx_training_result (result)
) ENGINE=InnoDB;

-- Model training metadata
CREATE TABLE IF NOT EXISTS model_training_runs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  model_name VARCHAR(100) NOT NULL,
  model_version VARCHAR(50) NOT NULL,
  training_start TIMESTAMP NOT NULL,
  training_end TIMESTAMP NOT NULL,
  training_duration INT,  -- in seconds
  
  -- Metrics
  ndcg_at_1 DECIMAL(5,4),
  ndcg_at_3 DECIMAL(5,4),
  ndcg_at_4 DECIMAL(5,4),
  accuracy DECIMAL(5,4),
  precision DECIMAL(5,4),
  recall DECIMAL(5,4),
  f1_score DECIMAL(5,4),
  mse DECIMAL(10,6),
  
  -- Training data info
  training_samples INT,
  validation_samples INT,
  test_samples INT,
  
  -- Model parameters
  parameters JSON,
  
  -- Git info
  commit_hash VARCHAR(40),
  branch VARCHAR(50),
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_model_training (model_name, model_version),
  INDEX idx_training_time (training_start)
) ENGINE=InnoDB;

-- Model predictions (for monitoring)
CREATE TABLE IF NOT EXISTS model_predictions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  model_name VARCHAR(100) NOT NULL,
  model_version VARCHAR(50) NOT NULL,
  race_id VARCHAR(50) NOT NULL,
  horse_id VARCHAR(50) NOT NULL,
  
  -- Prediction outputs
  prediction_probability DECIMAL(5,4) NOT NULL,
  confidence DECIMAL(5,4),
  
  -- Actual result (if available)
  actual_result INT,
  actual_finishing_position INT,
  
  -- Timing
  prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  resolved_time TIMESTAMP NULL,
  
  -- Metadata
  input_features JSON,
  
  INDEX idx_prediction_model (model_name, model_version),
  INDEX idx_prediction_race (race_id),
  INDEX idx_prediction_time (prediction_time)
) ENGINE=InnoDB;

-- Data drift monitoring
CREATE TABLE IF NOT EXISTS data_drift_metrics (
  id INT AUTO_INCREMENT PRIMARY KEY,
  feature_name VARCHAR(100) NOT NULL,
  
  -- Statistical metrics
  mean_training DECIMAL(20,10),
  mean_production DECIMAL(20,10),
  std_training DECIMAL(20,10),
  std_production DECIMAL(20,10),
  
  -- Drift detection
  kl_divergence DECIMAL(20,10),
  js_divergence DECIMAL(20,10),
  wasserstein_distance DECIMAL(20,10),
  
  -- Alerting
  drift_detected BOOLEAN DEFAULT FALSE,
  drift_severity VARCHAR(20),  -- 'low', 'medium', 'high'
  
  -- Timing
  calculation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_drift_feature (feature_name),
  INDEX idx_drift_time (calculation_time)
) ENGINE=InnoDB;
