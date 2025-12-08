from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
from scripts.model_utils import load_models, score_batch
from scripts.file_processor import process_uploaded_file
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# In-memory storage for recent results
RESULTS = []

# Load models and scaler
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'latest_model.joblib')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'latest_scaler.joblib')

print(f"🔍 Looking for model at: {os.path.abspath(MODEL_PATH)}")
print(f"🔍 Looking for scaler at: {os.path.abspath(SCALER_PATH)}")

# Load models at startup
load_models(MODEL_PATH, SCALER_PATH)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route('/api/score_csv', methods=['POST'])
def score_csv():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in the request."}), 400
    
    f = request.files['file']
    if f.filename == '':
        return jsonify({"success": False, "error": "No file selected."}), 400

    try:
        print(f"Processing file: {f.filename}")
        
        # Process the uploaded file
        df = process_uploaded_file(f)
        print(f"Processed file. Rows: {len(df)}, Columns: {df.columns.tolist()}")
        
        # Extract numeric columns or use text features
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        print(f"Numeric columns: {numeric_cols}")
        
        if not numeric_cols and 'text' in df.columns:
            numeric_cols = ['length', 'word_count']
            if not all(col in df.columns for col in numeric_cols):
                error_msg = "Could not extract suitable features from the file. No numeric columns found."
                print(error_msg)
                return jsonify({"success": False, "error": error_msg}), 400

        # Score the data
        print("Scoring data...")
        results = score_batch(df[numeric_cols])
        print("Scoring complete.")
        
        # Merge results with original data
        merged = pd.concat([df.reset_index(drop=True), results.reset_index(drop=True)], axis=1)
        
        # Convert timestamp to string for JSON serialization
        for col in merged.select_dtypes(include=['datetime64']).columns:
            merged[col] = merged[col].astype(str)
        
        # Get top anomalies
        top = merged.sort_values(by="score", ascending=False).head(50).to_dict(orient="records")
        
        # Ensure all values are JSON serializable
        for r in top:
            r['_timestamp'] = datetime.utcnow().isoformat()
            for k, v in r.items():
                if pd.isna(v):
                    r[k] = None
                elif isinstance(v, (pd.Timestamp, datetime)):
                    r[k] = v.isoformat()

        # Update global results
        global RESULTS
        RESULTS = top + RESULTS[:100]  # Keep only the 100 most recent results
        
        # Calculate anomaly count
        anomaly_count = len(merged[merged['score'] > 0.7]) if 'score' in merged.columns else 0
        
        # Prepare response
        response = {
            "success": True,
            "count": len(merged),
            "file_type": os.path.splitext(f.filename)[1],
            "features_used": numeric_cols,
            "results_preview": top[:10],  # Send first 10 results for preview
            "stats": {
                "total_records": len(merged),
                "anomaly_threshold": 0.7,
                "anomaly_count": anomaly_count
            },
            "message": f"Successfully analyzed {len(merged)} records. Found {anomaly_count} anomalies."
        }
        
        print(f"Analysis complete. Found {anomaly_count} anomalies out of {len(merged)} records.")
        return jsonify(response)
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error processing file: {error_msg}")
        print(error_trace)
        return jsonify({
            "success": False, 
            "error": error_msg,
            "trace": error_trace if app.debug else None
        }), 500

@app.route("/api/recent")
def get_recent():
    """Return recent anomalies."""
    return jsonify({
        "success": True,
        "recent": RESULTS[:10]  # Return only the 10 most recent anomalies
    })

@app.route("/api/stats")
def get_stats():
    """Return statistics about the analysis."""
    return jsonify({
        "success": True,
        "totalScans": len(RESULTS),
        "threatsDetected": len([r for r in RESULTS if r.get('score', 0) > 0.7])
    })

# @app.route("/api/score_csv", methods=["POST"])
# def score_csv():
#     """Handle file uploads of different types and return anomaly scores."""
#     if 'file' not in request.files:
#         return jsonify({"error": "No file part in the request."}), 400
    
#     f = request.files['file']
#     if f.filename == '':
#         return jsonify({"error": "No file selected."}), 400

#     try:
#         # Process the uploaded file
#         df = process_uploaded_file(f)
        
#         # Get numeric columns for the model
#         numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
#         # If no numeric columns, try to use text features
#         if not numeric_cols and 'text' in df.columns:
#             numeric_cols = ['length', 'word_count']
#             if not all(col in df.columns for col in numeric_cols):
#                 return jsonify({
#                     "error": "Could not extract suitable features from the file.",
#                     "suggestions": "Try uploading a file with numeric data or a different format."
#                 }), 400

#         # Score the data
#         results = score_batch(df[numeric_cols])
        
#         # Combine results with original data
#         merged = pd.concat([df.reset_index(drop=True), 
#                           results.reset_index(drop=True)], axis=1)
        
#         # Store top anomalies
#         top = merged.sort_values(by="score", ascending=False).head(50).to_dict(orient="records")
#         for r in top:
#             r['_timestamp'] = datetime.utcnow().isoformat()
        
#         # Store in memory
#         global RESULTS
#         RESULTS[:0] = top  # Prepend new results
        
#         # Prepare response
#         response = {
#     "success": True,
#     "count": len(merged),
#     "file_type": os.path.splitext(f.filename)[1],
#     "features_used": numeric_cols,
#     "results_preview": top[:10],  # Top 10 anomalies
#     "stats": {
#         "total_records": len(merged),
#         "anomaly_threshold": 0.7,  # Example threshold
#         "anomaly_count": len(merged[merged['score'] > 0.7]) if 'score' in merged.columns else 0
#     },
#     "message": f"Processed {len(merged)} items from {f.filename}"
# }
        
#         return jsonify(response)
        
    # except Exception as e:
    #     return jsonify({
    #         "success": False,
    #         "error": "Failed to process file",
    #         "details": str(e)
    #     }), 500

@app.route("/api/recent", methods=["GET"])
def recent():
    """Return recent anomalies."""
    return jsonify({"recent": RESULTS[:50]})

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files."""
    return send_from_directory('static', path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)












# import os
# from flask import Flask, request, jsonify, render_template
# from scripts.model_utils import load_models, score_batch
# from scripts.file_processor import process_uploaded_file
# from datetime import datetime
# import pandas as pd

# app = Flask(__name__, static_folder="static", template_folder="templates")
# CORS(app)

# # Get the absolute path to the models directory
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# MODEL_DIR = os.path.join(BASE_DIR, 'models')

# # Use the latest model and scaler files
# MODEL_PATH = os.path.join(MODEL_DIR, 'latest_model.joblib')
# SCALER_PATH = os.path.join(MODEL_DIR, 'latest_scaler.joblib')

# print(f"🔍 Looking for model at: {MODEL_PATH}")
# print(f"🔍 Looking for scaler at: {SCALER_PATH}")
# load_models(MODEL_PATH, SCALER_PATH)

# # In-memory store of latest results (for demo)
# RESULTS = []

# @app.route("/")
# def index():
#     return render_template("index.html")

# @app.route("/api/score_csv", methods=["POST"])
# def score_csv():
#     """
#     Accepts file upload form-data with key 'file' (CSV). Returns scoring results.
#     """
#     print("\n=== New File Upload Request ===")
#     print("Request headers:", dict(request.headers))
#     print("Form data:", request.form)
#     print("Files received:", request.files)
    
#     # Check if the post request has the file part
#     if 'file' not in request.files:
#         print("Error: No 'file' in request.files")
#         return jsonify({"error": "No file part in the request.", "request_files": str(request.files)}), 400
    
#     f = request.files['file']
    
#     # If user does not select file, browser also
#     # submit an empty part without filename
#     if f.filename == '':
#         print("Error: No selected file")
#         return jsonify({"error": "No file selected.", "file_info": str(f)}), 400
    
#     print(f"File info - Name: {f.filename}, Content-Type: {f.content_type}")
    
#     try:
#         print("Attempting to read CSV file...")
#         # Save the file temporarily
#         import tempfile
#         import os
        
#         # Create a temporary file
#         temp_dir = tempfile.mkdtemp()
#         temp_path = os.path.join(temp_dir, f.filename)
#         f.save(temp_path)
#         print(f"File saved temporarily to: {temp_path}")
        
#         # Read the CSV file
#         try:
#             df = pd.read_csv(temp_path)
#             print(f"Successfully read CSV with {len(df)} rows and {len(df.columns)} columns")
#             print("Columns:", df.columns.tolist())
            
#             # Ensure we have data to process
#             if len(df) == 0:
#                 return jsonify({"error": "The CSV file is empty."}), 400
                
#             # Check if we have any numeric columns
#             numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
#             if not numeric_cols:
#                 return jsonify({
#                     "error": "No numeric columns found in the CSV file.",
#                     "available_columns": df.columns.tolist()
#                 }), 400
            
#             print("Scoring batch...")
#             results = score_batch(df[numeric_cols])  # Only pass numeric columns
#             print("Scoring completed")
            
#             # Convert results to a format that can be JSON serialized
#             merged = pd.concat([df.reset_index(drop=True), results.reset_index(drop=True)], axis=1)
            
#             # Store top anomalies in memory
#             top = merged.sort_values(by="score").head(50).to_dict(orient="records")
#             for r in top:
#                 r['_timestamp'] = datetime.utcnow().isoformat()
#             RESULTS[:0] = top  # prepend
            
#             response = {
#                 "count": len(merged), 
#                 "results_preview": top[:10],
#                 "message": f"Processed {len(merged)} rows with {len(numeric_cols)} numeric features"
#             }
#             print("Returning response with", len(merged), "rows")
#             return jsonify(response)
            
#         except pd.errors.EmptyDataError:
#             return jsonify({"error": "The file appears to be empty or not a valid CSV"}), 400
            
#         except pd.errors.ParserError as e:
#             return jsonify({"error": f"Error parsing CSV: {str(e)}"}), 400
            
#         finally:
#             # Clean up the temporary file
#             try:
#                 os.remove(temp_path)
#                 os.rmdir(temp_dir)
#             except Exception as e:
#                 print(f"Warning: Could not remove temporary file: {e}")
        
#     except Exception as e:
#         import traceback
#         error_msg = str(e)
#         error_trace = traceback.format_exc()
#         print(f"Error processing file: {error_msg}")
#         print(error_trace)
#         return jsonify({
#             "error": "Failed to process file",
#             "details": error_msg,
#             "hint": "Please ensure the file is a valid CSV with numeric data",
#             "trace": error_trace.split('\n')
#         }), 500

# @app.route("/api/score_csv", methods=["POST"])
# def score_csv():
#     """Handle file uploads of different types and return anomaly scores."""
#     if 'file' not in request.files:
#         return jsonify({"error": "No file part in the request."}), 400
    
#     f = request.files['file']
#     if f.filename == '':
#         return jsonify({"error": "No file selected."}), 400

#     try:
#         # Process the uploaded file
#         df = process_uploaded_file(f)
        
#         # Get numeric columns for the model
#         numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
#         # If no numeric columns, try to use text features
#         if not numeric_cols and 'text' in df.columns:
#             numeric_cols = ['length', 'word_count']
#             if not all(col in df.columns for col in numeric_cols):
#                 return jsonify({
#                     "error": "Could not extract suitable features from the file.",
#                     "suggestions": "Try uploading a file with numeric data or a different format."
#                 }), 400

#         # Score the data
#         results = score_batch(df[numeric_cols])
        
#         # Combine results with original data
#         merged = pd.concat([df.reset_index(drop=True), 
#                           results.reset_index(drop=True)], axis=1)
        
#         # Store top anomalies
#         top = merged.sort_values(by="score").head(50).to_dict(orient="records")
#         for r in top:
#             r['_timestamp'] = datetime.utcnow().isoformat()
        
#         # Store in memory
#         RESULTS[:0] = top
        
#         # Prepare response
#         response = {
#             "success": True,
#             "count": len(merged),
#             "file_type": os.path.splitext(f.filename)[1],
#             "features_used": numeric_cols,
#             "results_preview": top[:10],
#             "message": f"Processed {len(merged)} items from {f.filename}"
#         }
        
#         return jsonify(response)
        
#     except Exception as e:
#         return jsonify({
#             "success": False,
#             "error": "Failed to process file",
#             "details": str(e)
#         }), 500

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)
