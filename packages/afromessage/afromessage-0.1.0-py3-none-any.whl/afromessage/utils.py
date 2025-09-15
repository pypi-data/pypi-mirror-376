import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_error(err):
    """Handle API errors"""
    if hasattr(err, 'response') and err.response is not None:
        logger.error("❌ API Error Details: %s", {
            'status': err.response.status_code,
            'data': err.response.text,
            'headers': dict(err.response.headers),
        })
        return Exception(
            f"API Error: {err.response.status_code} - {err.response.text}"
        )
    logger.error("❌ Network Error: %s", str(err))
    return Exception(f"Network Error: {str(err)}")

def log_request(endpoint, method, payload):
    """Log API requests"""
    logger.info("📤 [%s] Request to: %s", method.upper(), endpoint)
    logger.info("   Payload: %s", json.dumps(payload, indent=2))

def log_response(endpoint, response):
    """Log API responses"""
    logger.info("📥 Response from: %s", endpoint)
    logger.info("   Data: %s", json.dumps(response, indent=2))