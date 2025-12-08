# web/app.py
"""
Flask web application for Network Traffic Anomaly Detection
"""
from flask import Flask, render_template, request, jsonify
import os
import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from anomaly_detection.scripts.predicts import AnomalyDetector

app = Flask(__name__)
# Increase maximum file upload size to 1GB
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB limit

def get_anomaly_detector():
    """Initialize and return the anomaly detector."""
    if not hasattr(get_anomaly_detector, 'detector'):
        get_anomaly_detector.detector = AnomalyDetector()
    return get_anomaly_detector.detector

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Get or create anomaly detector
        detector = get_anomaly_detector()
        
        # Detect anomalies
        result = detector.detect_anomaly(data)
        
        # Prepare response with severity information
        response = {
            'status': 'success',
            'is_anomaly': result['is_anomaly'],
            'score': result['anomaly_score'],
            'severity': result.get('severity', 'low'),
            'timestamp': result['timestamp']
        }
        
        # Add feature details for debugging (limit to first 5 features)
        if 'features' in result:
            response['features'] = {k: v for i, (k, v) in enumerate(result['features'].items()) if i < 5}
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in detect endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
