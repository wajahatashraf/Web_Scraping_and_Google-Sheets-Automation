import gspread
from google.oauth2.service_account import Credentials
import os
import json
import re

# Read service account JSON from environment variable
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not SERVICE_ACCOUNT_JSON:
    raise ValueError("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set")

SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_JSON)

# Scopes required for Sheets access
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Google Sheet ID
SPREADSHEET_ID = "1zJulE6Jdp90nyP9-0P90nqrY2NFcTK93ChcWoKduups"

# Path to config.py (same folder)
CONFIG_FILE = "config.py"


def update_config(creds_dict):
    """Update config.py with new username/password values."""
    with open(CONFIG_FILE, "r") as f:
        config_text = f.read()

    replacements = {
        "CSTOREPRO_USERNAME": creds_dict.get("CStorePro Username"),
        "CSTOREPRO_PASSWORD": creds_dict.get("CStorePro Password"),
        "COLUMBUSDATA_USERNAME": creds_dict.get("ColumbusData Username"),
        "COLUMBUSDATA_PASSWORD": creds_dict.get("ColumbusData Password"),
    }

    updated_text = config_text
    for key, value in replacements.items():
        if value is None:
            continue
        pattern = rf'{key}\s*=\s*"(.*?)"'
        updated_text = re.sub(pattern, f'{key} = "{value}"', updated_text)

    with open(CONFIG_FILE, "w") as f:
        f.write(updated_text)
    print("✅ config.py updated successfully!")


def fetch_and_delete_credentials():
    """Fetch credentials from the Google Sheet, delete sheet, and update config."""

    credentials = Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO, scopes=SCOPES
    )
    client = gspread.authorize(credentials)

    sheet = client.open_by_key(SPREADSHEET_ID)

    try:
        cred_sheet = sheet.worksheet("Credentials")
    except gspread.exceptions.WorksheetNotFound:
        print("⚠️ No 'Credentials' sheet found — skipping update.")
        return None

    data = cred_sheet.get_all_values()
    if len(data) < 2:
        print("⚠️ No credentials found — skipping update.")
        return None

    headers = data[0]
    values = data[1]
    creds_dict = dict(zip(headers, values))
    print("📥 Retrieved credentials from Google Sheet")

    update_config(creds_dict)

    sheet.del_worksheet(cred_sheet)
    print("🗑️ Deleted the 'Credentials' sheet after reading.")
    return creds_dict


if __name__ == "__main__":
    creds = fetch_and_delete_credentials()
    if creds:
        print("✔ Done")
