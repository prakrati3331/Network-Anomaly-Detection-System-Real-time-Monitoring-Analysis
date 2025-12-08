"""
train.py - Script for training the Isolation Forest model for anomaly detection
"""

import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

def load_and_preprocess(data_path, drop_cols=None):
    """
    Load and preprocess the dataset
    
    Args:
        data_path (str): Path to the dataset CSV file
        drop_cols (list): List of columns to drop
        
    Returns:
        tuple: (X_scaled, y, feature_names)
    """
    print(f"📊 Loading data from {data_path}...")
    try:
        df = pd.read_csv(data_path)
        
        # Drop non-numeric columns or specific columns if provided
        if drop_cols:
            df = df.drop(columns=drop_cols, errors='ignore')
            
        # Ensure all data is numeric
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col])
                except:
                    df = df.drop(columns=[col])
                    
        return df
        
    except Exception as e:
        print(f"❌ Error loading data: {str(e)}")
        raise

def train():
    """
    Main training function that loads data, trains the model, and saves it
    """
    try:
        # Configuration
        # Get the absolute path to the data directory
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DATA_PATH = os.path.join(BASE_DIR, 'data', 'cicids2017_cleaned.csv')
        MODEL_DIR = os.path.join(BASE_DIR, 'models')
        os.makedirs(MODEL_DIR, exist_ok=True)
        
        # Columns to drop (if any)
        DROP_COLS = ['label']  # Adjust based on your dataset
        
        # Load and preprocess data
        print("🔍 Preprocessing data...")
        df = load_and_preprocess(DATA_PATH, DROP_COLS)
        
        # Separate features and target if exists
        if 'label' in df.columns:
            X = df.drop(columns=['label'])
            y = df['label']
        else:
            X = df
            y = None
            
        # Scale the features
        print("⚖️  Scaling features...")
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train the model
        print("🤖 Training Isolation Forest model...")
        model = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination=0.1,  # Adjust based on your data
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_scaled)
        
        # Save the model and scaler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(MODEL_DIR, f'isolation_forest_{timestamp}.joblib')
        scaler_path = os.path.join(MODEL_DIR, f'scaler_{timestamp}.joblib')
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        # Create copies for the latest model and scaler
        latest_model = os.path.join(MODEL_DIR, 'latest_model.joblib')
        latest_scaler = os.path.join(MODEL_DIR, 'latest_scaler.joblib')
        
        # Remove existing files if they exist
        for file_path in [latest_model, latest_scaler]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"⚠️ Could not remove {file_path}: {str(e)}")
        
        # Copy the files instead of creating symlinks
        import shutil
        shutil.copy2(model_path, latest_model)
        shutil.copy2(scaler_path, latest_scaler)
        
        print(f"✅ Model saved to {model_path}")
        print(f"✅ Scaler saved to {scaler_path}")
        
        # If we have labels, evaluate the model
        if y is not None:
            print("📊 Evaluating model...")
            y_pred = model.predict(X_scaled)
            y_pred = [1 if x == -1 else 0 for x in y_pred]  # Convert to binary (1=anomaly, 0=normal)
            
            from sklearn.metrics import classification_report, confusion_matrix
            
            print("\n📈 Classification Report:")
            print(classification_report(y, y_pred, target_names=['Normal', 'Anomaly']))
            
            # Plot confusion matrix
            plt.figure(figsize=(8, 6))
            cm = confusion_matrix(y, y_pred)
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                        xticklabels=['Normal', 'Anomaly'],
                        yticklabels=['Normal', 'Anomaly'])
            plt.xlabel('Predicted')
            plt.ylabel('Actual')
            plt.title('Confusion Matrix')
            
            # Save the plot
            OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs')
            os.makedirs(OUTPUTS_DIR, exist_ok=True)
            plot_path = os.path.join(OUTPUTS_DIR, 'confusion_matrix.png')
            plt.savefig(plot_path)
            print(f"📊 Confusion matrix saved to {plot_path}")
        
        return model, scaler
        
    except Exception as e:
        print(f"❌ Error during training: {str(e)}")
        raise

if __name__ == "__main__":
    # This allows the script to be run directly as well
    train()
