#!/usr/bin/env python3
"""
Training Data Loader for Equine Oracle ML Pipeline

This script loads and prepares training data from various sources:
1. Local CSV files
2. Database (MySQL)
3. S3 buckets
4. Synthetic data generation
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)


class TrainingDataLoader:
    """Loads and prepares training data for ML models"""
    
    def __init__(self, data_dir='ml/data', output_file='training_data.csv'):
        self.data_dir = Path(data_dir)
        self.output_file = self.data_dir / output_file
        self.data_sources = []
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_from_csv(self, filepath=None):
        """Load training data from CSV file"""
        if filepath is None:
            filepath = self.data_dir / 'training_data.csv'
        else:
            filepath = Path(filepath)
        
        if not filepath.exists():
            logger.warning(f"CSV file not found: {filepath}")
            return None
        
        logger.info(f"Loading training data from {filepath}")
        
        try:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} samples from CSV")
            self.data_sources.append(f"csv:{filepath}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return None
    
    def load_from_database(self, db_config=None):
        """Load training data from MySQL database"""
        if db_config is None:
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 3306)),
                'user': os.getenv('DB_USER', 'ml_user'),
                'password': os.getenv('DB_PASSWORD', 'ml_password'),
                'database': os.getenv('DB_NAME', 'equine_oracle_training')
            }
        
        try:
            import mysql.connector
            from mysql.connector import Error
            
            logger.info(f"Connecting to database: {db_config['host']}")
            
            connection = mysql.connector.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            
            if connection.is_connected():
                logger.info("Successfully connected to database")
                
                # Load training data
                query = "SELECT * FROM training_data"
                df = pd.read_sql(query, connection)
                
                logger.info(f"Loaded {len(df)} samples from database")
                self.data_sources.append(f"db:{db_config['host']}/{db_config['database']}")
                
                connection.close()
                return df
            
        except ImportError:
            logger.warning("mysql-connector-python not installed. Install with: pip install mysql-connector-python")
        except Error as e:
            logger.error(f"Database error: {e}")
        
        return None
    
    def load_from_s3(self, bucket_name, prefix='training/'):
        """Load training data from S3"""
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError, ClientError
            
            s3 = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            
            logger.info(f"Loading training data from S3: {bucket_name}/{prefix}")
            
            # List objects in the bucket
            response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            
            dfs = []
            for obj in response.get('Contents', []):
                if obj['Key'].endswith('.csv'):
                    # Download file
                    local_path = self.data_dir / Path(obj['Key']).name
                    s3.download_file(bucket_name, obj['Key'], str(local_path))
                    
                    # Load CSV
                    df = pd.read_csv(local_path)
                    dfs.append(df)
                    logger.info(f"Loaded {len(df)} samples from {obj['Key']}")
                    self.data_sources.append(f"s3:{bucket_name}/{obj['Key']}")
            
            if dfs:
                combined_df = pd.concat(dfs, ignore_index=True)
                logger.info(f"Loaded {len(combined_df)} total samples from S3")
                return combined_df
            
        except ImportError:
            logger.warning("boto3 not installed. Install with: pip install boto3")
        except NoCredentialsError:
            logger.warning("AWS credentials not available")
        except ClientError as e:
            logger.error(f"S3 error: {e}")
        
        return None
    
    def generate_synthetic_data(self, n_samples=10000):
        """Generate synthetic training data for testing"""
        logger.info(f"Generating {n_samples} synthetic training samples")
        
        np.random.seed(42)
        
        # Generate base features
        data = {
            'race_id': [f'race_{i % 1000}' for i in range(n_samples)],
            'horse_id': [f'horse_{i % 500}' for i in range(n_samples)],
            
            # Race features
            'distance': np.random.choice([800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400], n_samples),
            'race_type': np.random.choice(['Maiden', 'Novice', 'Handicap', 'Stakes', 'Group 1', 'Group 2', 'Group 3'], n_samples),
            'track': np.random.choice(['Ellerslie', 'Te Rapa', 'Hastings', 'Trenholme', 'Riccarton', 'Wingatui'], n_samples),
            'surface': np.random.choice(['Turf', 'Synthetic', 'Dirt'], n_samples),
            
            # Horse features
            'horse_age': np.random.randint(2, 10, n_samples),
            'horse_sex': np.random.choice(['Colt', 'Filly', 'Gelding', 'Mare', 'Stallion'], n_samples),
            
            # Performance features
            'days_since_last_race': np.random.randint(7, 90, n_samples),
            'avg_finishing_position_5': np.random.uniform(1, 10, n_samples).round(2),
            'avg_finishing_position_10': np.random.uniform(1, 10, n_samples).round(2),
            'win_rate_5': np.random.uniform(0, 0.5, n_samples).round(4),
            'win_rate_10': np.random.uniform(0, 0.5, n_samples).round(4),
            'place_rate_5': np.random.uniform(0.3, 0.8, n_samples).round(4),
            'place_rate_10': np.random.uniform(0.3, 0.8, n_samples).round(4),
            
            # Jockey/Trainer features
            'jockey_win_rate': np.random.uniform(0.1, 0.4, n_samples).round(4),
            'trainer_win_rate': np.random.uniform(0.1, 0.4, n_samples).round(4),
            
            # Market features
            'odds': np.random.uniform(1, 20, n_samples).round(2),
            'implied_probability': np.random.uniform(0.05, 0.95, n_samples).round(4),
            
            # Additional engineered features
            'weighted_form_score': np.random.uniform(0, 100, n_samples).round(2),
            'speed_rating': np.random.uniform(50, 120, n_samples).round(2),
            'class_drop': np.random.randint(-2, 3, n_samples),
            'distance_suitability': np.random.uniform(0, 1, n_samples).round(4),
            'track_condition': np.random.choice(['Good', 'Soft', 'Heavy', 'Firm'], n_samples),
            'barrier': np.random.randint(1, 14, n_samples),
            'weight': np.random.uniform(50, 65, n_samples).round(2),
            
            # Time-based features
            'year': np.random.choice([2020, 2021, 2022, 2023, 2024, 2025], n_samples),
            'month': np.random.randint(1, 13, n_samples),
            'day': np.random.randint(1, 29, n_samples),
            'day_of_week': np.random.randint(0, 7, n_samples),
            'week_of_year': np.random.randint(1, 53, n_samples),
        }
        
        # Generate target variable (result) based on features
        # Higher probability of winning for horses with better features
        df = pd.DataFrame(data)
        
        # Calculate win probability based on features
        win_prob = (
            0.3 * (1 - df['avg_finishing_position_5'] / 10) +
            0.2 * df['win_rate_5'] +
            0.15 * df['jockey_win_rate'] +
            0.15 * df['trainer_win_rate'] +
            0.1 * (1 / df['odds']) +
            0.1 * df['implied_probability']
        )
        
        # Normalize and create binary target
        win_prob = (win_prob - win_prob.min()) / (win_prob.max() - win_prob.min())
        df['result'] = (win_prob > np.random.uniform(0, 1, n_samples)).astype(int)
        
        # Add finishing position (1-12)
        df['finishing_position'] = np.where(
            df['result'] == 1, 
            1,  # Winners finish first
            np.random.randint(2, 13, n_samples)  # Others finish 2-12
        )
        
        # Add more features based on result
        df['prev_race_won'] = (np.random.random(n_samples) > 0.7).astype(int)
        df['win_streak'] = np.where(df['result'] == 1, np.random.randint(0, 4, n_samples), 0)
        df['losing_streak'] = np.where(df['result'] == 0, np.random.randint(0, 6, n_samples), 0)
        
        # Add semantic features (placeholders for Grok-4 integration)
        df['grok4_jockey_form_score'] = np.random.uniform(0, 1, n_samples).round(4)
        df['grok4_trainer_momentum'] = np.random.uniform(-1, 1, n_samples).round(4)
        df['grok4_horse_fitness'] = np.random.uniform(0, 1, n_samples).round(4)
        
        # Add weather features
        df['track_moisture_pct'] = np.random.uniform(30, 90, n_samples).round(2)
        df['wind_speed_mph'] = np.random.uniform(0, 25, n_samples).round(2)
        df['temperature_f'] = np.random.uniform(40, 85, n_samples).round(2)
        df['precipitation_24h_mm'] = np.random.exponential(2, n_samples).round(2)
        
        # Add interaction features
        df['distance_x_perf'] = df['distance'] * (11 - df['avg_finishing_position_5'])
        df['distance_x_form'] = df['distance'] * df['weighted_form_score']
        df['odds_x_win_rate'] = df['odds'] * df['win_rate_5']
        
        logger.info(f"Generated synthetic data with {len(df.columns)} features")
        self.data_sources.append(f"synthetic:{n_samples}")
        
        return df
    
    def preprocess_data(self, df):
        """Preprocess and clean training data"""
        logger.info("Preprocessing training data...")
        
        # Drop duplicates
        initial_count = len(df)
        df = df.drop_duplicates()
        logger.info(f"Dropped {initial_count - len(df)} duplicates")
        
        # Handle missing values
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                # Fill numeric columns with median
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
            else:
                # Fill categorical columns with mode
                mode_val = df[col].mode()[0] if not df[col].mode().empty else 'Unknown'
                df[col] = df[col].fillna(mode_val)
        
        # Convert categorical variables
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if col not in ['race_id', 'horse_id']:  # Don't encode IDs
                df = pd.get_dummies(df, columns=[col], drop_first=True)
        
        # Ensure target variable exists
        if 'result' not in df.columns:
            # Create result from finishing_position if available
            if 'finishing_position' in df.columns:
                df['result'] = (df['finishing_position'] == 1).astype(int)
            else:
                # Create random result
                df['result'] = np.random.randint(0, 2, len(df))
        
        logger.info(f"Preprocessed data: {len(df)} samples, {len(df.columns)} features")
        
        return df
    
    def split_data(self, df, test_size=0.2, val_size=0.1):
        """Split data into training, validation, and test sets"""
        from sklearn.model_selection import train_test_split
        
        logger.info("Splitting data into train/val/test sets...")
        
        # Split into train+val and test
        train_val, test = train_test_split(
            df, 
            test_size=test_size, 
            random_state=42,
            stratify=df['result'] if 'result' in df.columns else None
        )
        
        # Split train+val into train and val
        train, val = train_test_split(
            train_val,
            test_size=val_size / (1 - test_size),
            random_state=42,
            stratify=train_val['result'] if 'result' in train_val.columns else None
        )
        
        logger.info(f"Train: {len(train)} samples")
        logger.info(f"Validation: {len(val)} samples")
        logger.info(f"Test: {len(test)} samples")
        
        return train, val, test
    
    def save_data(self, df, filename=None):
        """Save training data to CSV"""
        if filename is None:
            filename = self.output_file
        else:
            filename = Path(filename)
        
        logger.info(f"Saving training data to {filename}")
        df.to_csv(filename, index=False)
        return filename
    
    def load_and_prepare(self, sources=['synthetic'], n_synthetic=10000):
        """Load and prepare training data from multiple sources"""
        dfs = []
        
        for source in sources:
            if source == 'csv':
                df = self.load_from_csv()
                if df is not None:
                    dfs.append(df)
            elif source == 'database':
                df = self.load_from_database()
                if df is not None:
                    dfs.append(df)
            elif source.startswith('s3:'):
                bucket = source[3:]
                df = self.load_from_s3(bucket)
                if df is not None:
                    dfs.append(df)
            elif source == 'synthetic':
                df = self.generate_synthetic_data(n_synthetic)
                dfs.append(df)
        
        if not dfs:
            logger.warning("No data loaded from any source, generating synthetic data")
            dfs.append(self.generate_synthetic_data(n_synthetic))
        
        # Combine all data sources
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Preprocess
        processed_df = self.preprocess_data(combined_df)
        
        # Save
        self.save_data(processed_df)
        
        return processed_df


def main():
    """Main function to load training data"""
    parser = argparse.ArgumentParser(description='Load training data for Equine Oracle ML')
    parser.add_argument('--sources', nargs='+', default=['synthetic'],
                        help='Data sources to use: csv, database, s3:bucket-name, synthetic')
    parser.add_argument('--n-synthetic', type=int, default=10000,
                        help='Number of synthetic samples to generate')
    parser.add_argument('--output', type=str, default='training_data.csv',
                        help='Output CSV filename')
    parser.add_argument('--split', action='store_true',
                        help='Split data into train/val/test sets')
    
    args = parser.parse_args()
    
    # Initialize loader
    loader = TrainingDataLoader(output_file=args.output)
    
    # Load and prepare data
    df = loader.load_and_prepare(args.sources, args.n_synthetic)
    
    if args.split:
        # Split data
        train, val, test = loader.split_data(df)
        
        # Save splits
        loader.save_data(train, 'training_data_train.csv')
        loader.save_data(val, 'training_data_val.csv')
        loader.save_data(test, 'training_data_test.csv')
        
        logger.info("Data splits saved successfully")
    
    logger.info(f"Training data loaded successfully: {len(df)} samples")
    logger.info(f"Data sources: {', '.join(loader.data_sources)}")


if __name__ == '__main__':
    main()
