import os
import shutil
import threading
import asyncio
import subprocess
from flask import Flask, jsonify
from flask_cors import CORS

from credntial import fetch_and_delete_credentials
from columbusdata_scrape import run_scraper
from upload import update_google_sheets

app = Flask(__name__)
CORS(app)  # allow requests from any origin

DATA_DIR = os.path.join(os.getcwd(), "data")
PLAYWRIGHT_CACHE = os.path.expanduser("~/.cache/ms-playwright")


def cleanup_data_folder():
    """Delete the data folder if exists."""
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)
        print(f"🗑️ Deleted existing folder: {DATA_DIR}")
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"📂 Created fresh folder: {DATA_DIR}")


def install_playwright_if_needed():
    """Install only Chromium if missing to save time."""
    chromium_path = os.path.join(PLAYWRIGHT_CACHE, "chromium")
    if not os.path.exists(chromium_path) or not os.listdir(chromium_path):
        print("⚠️ Chromium not found. Installing only Chromium...")
        subprocess.run(["playwright", "install", "chromium"], check=True)
        print("✅ Chromium installed.")
    else:
        print("✅ Chromium already installed. Skipping installation.")


def run_workflow_sync():
    """Wrapper to run async scraper in a thread with pre/post cleanup."""
    try:
        # --- Install Playwright Chromium only if needed ---
        install_playwright_if_needed()

        # --- Cleanup before scraping ---
        cleanup_data_folder()

        print("🔄 Checking Google Sheet for new credentials...")
        fetch_and_delete_credentials()  # ensures GOOGLE_APPLICATION_CREDENTIALS_JSON is set

        print("🚀 Starting Columbus scraper now...")
        # Run async Playwright scraper in sync context
        asyncio.run(run_scraper())

        print("🚀 Updating Google Sheets now...")
        update_google_sheets(DATA_DIR)

        print("✅ Workflow completed successfully.")

    except Exception as e:
        print(f"❌ Error during workflow: {e}")

    finally:
        # --- Cleanup after everything ---
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
            print(f"🗑️ Deleted folder after workflow: {DATA_DIR}")


@app.route('/run-scraper', methods=['GET'])
def run_scraper_endpoint():
    """Flask endpoint to trigger the scraper and Google Sheets update."""
    thread = threading.Thread(target=run_workflow_sync, daemon=True)
    thread.start()
    return jsonify({
        "status": "started",
        "message": "Scraper and Google Sheets update started in background"
    }), 200


@app.route('/', methods=['GET'])
def home():
    """Health check / welcome endpoint."""
    return jsonify({
        "status": "ok",
        "message": "Columbus Scraper API is running"
    }), 200


if __name__ == "__main__":
    # Run Flask server on Railway or local
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
