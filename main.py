from flask import Flask, jsonify
from credntial import fetch_and_delete_credentials
from columbusdata_scrape import run_scraper
import config
from upload import update_google_sheets
import threading
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow requests from any origin

def run_all_tasks():
    """Runs the full scraping and Google Sheets update workflow."""
    try:
        print("🔄 Checking Google Sheet for new credentials...")
        fetch_and_delete_credentials()

        print("🚀 Starting Columbus scraper now...")
        run_scraper()

        print("🚀 Updating Google Sheets now...")
        update_google_sheets('data')

        print("✅ Workflow completed successfully.")
    except Exception as e:
        print(f"❌ Error during workflow: {e}")

@app.route('/run-scraper', methods=['GET'])
def run_scraper_endpoint():
    """Flask endpoint to trigger the scraper and Google Sheets update."""
    # Run the workflow in a separate thread so Flask response is immediate
    thread = threading.Thread(target=run_all_tasks)
    thread.start()
    return jsonify({"status": "started", "message": "Scraper and Google Sheets update started in background"}), 200

@app.route('/', methods=['GET'])
def home():
    """Health check / welcome endpoint."""
    return jsonify({"status": "ok", "message": "Columbus Scraper API is running"}), 200


if __name__ == "__main__":
    # Run Flask server
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
