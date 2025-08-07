#!/usr/bin/env python3

# Main entry point for the Sense 360 Zone Configurator
# Import the Flask app from backend.py and make it available for gunicorn

from backend import app

if __name__ == '__main__':
    # For development - use Flask's built-in server
    app.run(host='0.0.0.0', port=5000, debug=True)