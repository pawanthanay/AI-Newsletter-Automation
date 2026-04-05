"""
API Server — Provides a local endpoint to trigger the AI Newsletter pipeline.
Used by the Chrome Extension to run fetches on demand.
"""

import sys
import logging
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS

# Ensure src modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config_loader import load_config
from main import run_pipeline

app = Flask(__name__)
# Enable CORS so the Chrome Extension can make requests
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

@app.route('/generate', methods=['GET'])
def generate_newsletter():
    """Endpoint to trigger the live newsletter generation and delivery."""
    try:
        logger.info("🚀 Received trigger from Chrome Extension")
        config = load_config()
        
        # Run the pipeline (this fetches, filters, categorizes, generates HTML, and emails)
        success = run_pipeline(config)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Newsletter successfully fetched and sent to your email!"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to generate or send newsletter. Check the terminal logs."
            }), 500

    except Exception as e:
        logger.error(f"❌ API Error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint to verify server is running."""
    return jsonify({"status": "ok", "message": "Server is running"}), 200


if __name__ == '__main__':
    logger.info("==================================================")
    logger.info("🤖 AI Newsletter Local API Server Starting")
    logger.info("🌐 Listening on all interfaces (0.0.0.0:5000)")
    logger.info("==================================================")
    # Run server on all interfaces to ensure reachability
    app.run(host='0.0.0.0', port=5000, debug=False)
