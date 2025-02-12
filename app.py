# app.py

# Import necessary modules
from flask import Flask, request, jsonify
import subprocess
import logging

# Create the Flask application instance
app = Flask(__name__)

# Set up basic logging to output messages to the console
logging.basicConfig(level=logging.INFO)

# Define the endpoint that will trigger your scraper
@app.route("/run-scraper", methods=["POST"])
def run_scraper_endpoint():
    try:
        # Log that a request has been received
        app.logger.info("Received request to run scraper.")
        
        # Execute the scraper.py script using subprocess.
        # The 'python' command is used to run the script.
        # capture_output=True collects stdout and stderr.
        # text=True returns output as a string.
        # check=True raises an exception if the script exits with a non-zero status.
        result = subprocess.run(
            ["python", "scraper.py"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log successful execution
        app.logger.info("Scraper executed successfully.")
        
        # Return a JSON response with the output from scraper.py
        return jsonify({
            "status": "success",
            "output": result.stdout
        }), 200

    except subprocess.CalledProcessError as e:
        # Log and return an error if the subprocess fails
        app.logger.error("Error running scraper: %s", e.stderr)
        return jsonify({
            "status": "error",
            "error": e.stderr
        }), 500

    except Exception as ex:
        # Log and return any unexpected errors
        app.logger.error("Unexpected error: %s", str(ex))
        return jsonify({
            "status": "error",
            "error": str(ex)
        }), 500

# Run the Flask app if this file is executed directly.
if __name__ == "__main__":
    # The app will listen on all network interfaces (0.0.0.0) on port 5002.
    app.run(host="0.0.0.0", port=5002)
