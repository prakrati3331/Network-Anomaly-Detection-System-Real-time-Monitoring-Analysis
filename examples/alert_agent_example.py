"""
Example usage of the AlertAgent with the existing anomaly detection system.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import the AlertAgent
from anomaly_detection.scripts.alert_agent import AlertAgent

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Initialize the alert agent with OpenRouter
    try:
        alert_agent = AlertAgent(
            model="openai/gpt-3.5-turbo",  # You can change this to any model supported by OpenRouter
            base_url="https://openrouter.ai/api/v1"
        )
        print("✅ Alert agent initialized successfully with OpenRouter!")
    except Exception as e:
        print(f"❌ Failed to initialize alert agent: {e}")
        print("Please make sure you have set the OPENAI_API_KEY environment variable.")
        return
    
    # Example anomaly data
    example_anomaly = {
        "timestamp": "2025-12-08T22:30:45.123456",
        "anomaly_score": 0.95,
        "features": {
            "packet_size": 1450,
            "packet_count": 1500,
            "source_ip": "192.168.1.100",
            "destination_ip": "10.0.0.1",
            "protocol": "TCP",
            "port": 443
        },
        "model_used": "IsolationForest",
        "confidence": 0.92
    }
    
    # Generate and display the alert
    print("\nGenerating alert for anomaly...")
    alert = alert_agent.send_alert(
        anomaly_data=example_anomaly,
        recipients=["admin@example.com"]
    )
    
    print("\nAlert details:")
    print(f"- Timestamp: {alert['timestamp']}")
    print(f"- Recipients: {', '.join(alert['recipients'])}")
    print("\nAlert message:")
    print(alert['message'])

if __name__ == "__main__":
    main()
