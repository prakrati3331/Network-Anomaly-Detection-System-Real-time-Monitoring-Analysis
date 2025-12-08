# anomaly_detection/scripts/predicts.py
import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from .alert_agent import AlertAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AnomalyDetector:
    def __init__(self, model_dir: str = None):
        """
        Initialize the AnomalyDetector with the latest model and scaler.
        
        Args:
            model_dir: Directory containing the model and scaler files
        """
        self.model = None
        self.scaler = None
        # Initialize with the exact feature names from the training data (excluding 'Attack Type' and 'label')
        self.feature_names = [
            'Destination Port', 'Flow Duration', 'Total Fwd Packets', 
            'Total Length of Fwd Packets', 'Fwd Packet Length Max', 'Fwd Packet Length Min', 
            'Fwd Packet Length Mean', 'Fwd Packet Length Std', 'Bwd Packet Length Max', 
            'Bwd Packet Length Min', 'Bwd Packet Length Mean', 'Bwd Packet Length Std', 
            'Flow Bytes/s', 'Flow Packets/s', 'Flow IAT Mean', 'Flow IAT Std', 
            'Flow IAT Max', 'Flow IAT Min', 'Fwd IAT Total', 'Fwd IAT Mean', 
            'Fwd IAT Std', 'Fwd IAT Max', 'Fwd IAT Min', 'Bwd IAT Total', 
            'Bwd IAT Mean', 'Bwd IAT Std', 'Bwd IAT Max', 'Bwd IAT Min', 
            'Fwd Header Length', 'Bwd Header Length', 'Fwd Packets/s', 
            'Bwd Packets/s', 'Min Packet Length', 'Max Packet Length', 
            'Packet Length Mean', 'Packet Length Std', 'Packet Length Variance', 
            'FIN Flag Count', 'PSH Flag Count', 'ACK Flag Count', 
            'Average Packet Size', 'Subflow Fwd Bytes', 'Init_Win_bytes_forward', 
            'Init_Win_bytes_backward', 'act_data_pkt_fwd', 'min_seg_size_forward', 
            'Active Mean', 'Active Max', 'Active Min', 'Idle Mean', 'Idle Max', 'Idle Min'
        ]
        self.alert_agent = AlertAgent()
        self.model_dir = model_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'models'
        )
        self._load_latest_model()

    def _load_latest_model(self):
        """Load the most recent model and scaler from the models directory."""
        try:
            # Find the latest model and scaler files
            model_files = list(Path(self.model_dir).glob('isolation_forest_*.joblib'))
            if not model_files:
                raise FileNotFoundError("No model files found in the models directory")
            
            # Get the most recent model
            latest_model = max(model_files, key=os.path.getmtime)
            # Extract the full timestamp (everything after 'isolation_forest_' and before '.joblib')
            model_timestamp = latest_model.stem.replace('isolation_forest_', '')
            scaler_file = Path(self.model_dir) / f'scaler_{model_timestamp}.joblib'
            
            # Load the model and scaler
            self.model = joblib.load(latest_model)
            self.scaler = joblib.load(scaler_file)
            
            print(f"✅ Loaded model: {latest_model.name}")
            print(f"✅ Loaded scaler: {scaler_file.name}")
            
            # Verify the number of features matches the model's expectations
            if hasattr(self.model, 'n_features_in_') and len(self.feature_names) != self.model.n_features_in_:
                print(f"⚠️  Warning: Expected {self.model.n_features_in_} features, but have {len(self.feature_names)}")
                
            print(f"✅ Using feature names: {self.feature_names}")
            print(f"✅ Total features: {len(self.feature_names)}")
            
            print(f"✅ Model loaded with {len(self.feature_names)} features")
            
        except Exception as e:
            print(f"❌ Error loading model or scaler: {str(e)}")
            raise

    def preprocess_data(self, data: Dict[str, Any]) -> np.ndarray:
        """
        Preprocess the input data for prediction.
        
        Args:
            data: Dictionary containing feature values
            
        Returns:
            np.ndarray: Preprocessed data ready for prediction
        """
        try:
            # Log the incoming data for debugging
            print("\n📥 Received data:", {k: v for k, v in data.items() if k in self.feature_names})
            
            # Create a new dictionary with all features set to 0.0
            processed_data = {feature: 0.0 for feature in self.feature_names}
            
            # Update with provided values, converting to float and handling potential string values
            for key, value in data.items():
                if key in processed_data:
                    try:
                        processed_data[key] = float(value)
                    except (ValueError, TypeError):
                        print(f"⚠️  Could not convert value for {key} to float, using 0.0")
                        processed_data[key] = 0.0
                else:
                    print(f"⚠️  Ignoring unknown feature: {key}")
            
            # Convert to DataFrame with a single row
            df = pd.DataFrame([processed_data])
            
            # Ensure columns are in the correct order
            df = df[self.feature_names]
            
            # Log the preprocessed data for debugging
            print("🔧 Preprocessed data:", df.iloc[0].to_dict())
            
            # Scale the features if a scaler is available
            if self.scaler is not None:
                df_scaled = self.scaler.transform(df)
                print(f"📊 Scaled data (first 5 features): {df_scaled[0][:5]}")
            else:
                df_scaled = df.values
                print("⚠️  No scaler available, using raw values")
            
            return df_scaled
            
        except Exception as e:
            print(f"❌ Error preprocessing data: {str(e)}")
            raise

    def detect_anomaly(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect anomalies in the input data with severity levels.
        
        Args:
            data: Dictionary containing feature values
            
        Returns:
            Dict containing anomaly detection results with severity
        """
        try:
            # Preprocess the data
            processed_data = self.preprocess_data(data)
            
            # Make prediction
            score = self.model.decision_function(processed_data)[0]
            
            # Define thresholds (adjust these based on your needs)
            SEVERE_THRESHOLD = -0.15  # More negative = more severe
            MILD_THRESHOLD = -0.05    # Between -0.05 and -0.15 is mild
            
            # Determine anomaly status and severity
            is_anomaly = score < MILD_THRESHOLD
            if score < SEVERE_THRESHOLD:
                severity = "high"
            elif score < MILD_THRESHOLD:
                severity = "medium"
            else:
                severity = "low"
            
            # Create result dictionary
            result = {
                'is_anomaly': bool(is_anomaly),
                'anomaly_score': float(score),
                'severity': severity,
                'timestamp': datetime.now().isoformat(),
                'features': data
            }
            
            # Send alert if anomaly is detected
            if is_anomaly:
                alert_data = {
                    'timestamp': result['timestamp'],
                    'score': score,
                    'severity': severity,
                    'features': data,
                    'message': (
                        f"Anomaly detected with score: {score:.4f} "
                        f"(Severity: {severity.upper()})"
                    )
                }
                self.alert_agent.send_alert(alert_data)
            
            return result
            
        except Exception as e:
            print(f"❌ Error detecting anomaly: {str(e)}")
            raise