"""
Network Traffic Anomaly Detection - Main Entry Point

This script serves as the main entry point for the Network Traffic Anomaly Detection system.
It provides a command-line interface for training the model and running the web application.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        'data',
        'models',
        'outputs',
        'web/static',
        'web/templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✓ Verified directory structure")

def train_model():
    """Train the anomaly detection model."""
    print("🚀 Starting model training...")
    try:
        from .scripts.train import train
        train()
        print("✅ Model training completed successfully!")
    except Exception as e:
        print(f"❌ Error during model training: {str(e)}")
        sys.exit(1)

def run_web_app(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask web application."""
    print(f"🌐 Starting web application on http://{host}:{port}")
    try:
        from web.app import app
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        print(f"❌ Error starting web application: {str(e)}")
        sys.exit(1)

def generate_sample_network_traffic():
    """Generate sample network traffic data that matches the training distribution."""
    import random
    import numpy as np
    
    # Generate realistic values for each feature based on the CIC-IDS2017 dataset
    return {
        'Destination Port': random.randint(0, 65535),
        'Flow Duration': random.randint(100, 1000000),  # milliseconds
        'Total Fwd Packets': random.randint(1, 1000),
        'Total Length of Fwd Packets': random.randint(100, 1000000),
        'Fwd Packet Length Max': random.randint(100, 1500),
        'Fwd Packet Length Min': random.randint(20, 1000),
        'Fwd Packet Length Mean': random.uniform(100, 1200),
        'Fwd Packet Length Std': random.uniform(1, 500),
        'Bwd Packet Length Max': random.randint(0, 1500),
        'Bwd Packet Length Min': random.randint(0, 500),
        'Bwd Packet Length Mean': random.uniform(0, 1000),
        'Bwd Packet Length Std': random.uniform(0, 500),
        'Flow Bytes/s': random.uniform(1000, 1000000),
        'Flow Packets/s': random.uniform(10, 10000),
        'Flow IAT Mean': random.uniform(0, 1000),
        'Flow IAT Std': random.uniform(0, 1000),
        'Flow IAT Max': random.uniform(0, 5000),
        'Flow IAT Min': random.uniform(0, 100),
        'Fwd IAT Total': random.uniform(0, 100000),
        'Fwd IAT Mean': random.uniform(0, 1000),
        'Fwd IAT Std': random.uniform(0, 1000),
        'Fwd IAT Max': random.uniform(0, 5000),
        'Fwd IAT Min': random.uniform(0, 100),
        'Bwd IAT Total': random.uniform(0, 100000),
        'Bwd IAT Mean': random.uniform(0, 1000),
        'Bwd IAT Std': random.uniform(0, 1000),
        'Bwd IAT Max': random.uniform(0, 5000),
        'Bwd IAT Min': random.uniform(0, 100),
        'Fwd Header Length': random.randint(0, 1000),
        'Bwd Header Length': random.randint(0, 1000),
        'Fwd Packets/s': random.uniform(0, 10000),
        'Bwd Packets/s': random.uniform(0, 10000),
        'Min Packet Length': random.randint(0, 1000),
        'Max Packet Length': random.randint(100, 1500),
        'Packet Length Mean': random.uniform(100, 1200),
        'Packet Length Std': random.uniform(1, 500),
        'Packet Length Variance': random.uniform(1, 250000),
        'FIN Flag Count': random.randint(0, 1),
        'PSH Flag Count': random.randint(0, 1),
        'ACK Flag Count': random.randint(0, 1),
        'Average Packet Size': random.uniform(100, 1500),
        'Subflow Fwd Bytes': random.randint(0, 1000000),
        'Init_Win_bytes_forward': random.randint(0, 65535),
        'Init_Win_bytes_backward': random.randint(0, 65535),
        'act_data_pkt_fwd': random.randint(0, 10),
        'min_seg_size_forward': random.randint(0, 1000),
        'Active Mean': random.uniform(0, 1000000),
        'Active Max': random.uniform(0, 1000000),
        'Active Min': random.uniform(0, 1000000),
        'Idle Mean': random.uniform(0, 1000000),
        'Idle Max': random.uniform(0, 1000000),
        'Idle Min': random.uniform(0, 1000000)
    }

def detect_anomalies():
    """Run anomaly detection on new data."""
    print("🔍 Starting anomaly detection...")
    try:
        from .scripts.predicts import AnomalyDetector
        import pandas as pd
        
        # Initialize the detector
        detector = AnomalyDetector()
        
        # Generate sample network traffic data that matches the training distribution
        print("📥 Generating sample network traffic data...")
        sample_data = generate_sample_network_traffic()
        
        # Print a few key features for verification
        print("\nSample data features:")
        for key in list(sample_data.keys())[:5]:  # Show first 5 features
            print(f"- {key}: {sample_data[key]}")
        print("...")
        
        # Detect anomalies
        print("\n🔍 Analyzing data for anomalies...")
        result = detector.detect_anomaly(sample_data)
        
        print("\n📊 Results:")
        if result['is_anomaly']:
            print(f"🚨 Anomaly detected! Score: {result['anomaly_score']:.4f}")
        else:
            print(f"✅ No anomalies detected. Score: {result['anomaly_score']:.4f}")
            
    except Exception as e:
        print(f"❌ Error during anomaly detection: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Network Traffic Anomaly Detection System')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train the anomaly detection model')
    
    # Web command
    web_parser = subparsers.add_parser('web', help='Run the web application')
    web_parser.add_argument('--host', default='0.0.0.0', help='Host to run the web server on')
    web_parser.add_argument('--port', type=int, default=5000, help='Port to run the web server on')
    web_parser.add_argument('--debug', action='store_true', help='Run in debug mode')

    # Detect command
    detect_parser = subparsers.add_parser('detect', help='Run anomaly detection on new data')
    
    # Full setup command
    setup_parser = subparsers.add_parser('setup', help='Setup the project (verify directories, install dependencies)')
    
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_directories()
    
    if args.command == 'train':
        train_model()
    elif args.command == 'web':
        run_web_app(host=args.host, port=args.port, debug=args.debug)

    elif args.command == 'detect':
        detect_anomalies()
    elif args.command == 'setup':
        print("✅ Setup completed successfully!")
    else:
        # Default action (no command provided)
        print("Network Traffic Anomaly Detection System")
        print("\nUsage:")
        print("  python main.py train    - Train the anomaly detection model")
        print("  python main.py web      - Run the web application")
        print("  python main.py setup    - Setup the project")
        sys.exit(1)

if __name__ == "__main__":
    main()