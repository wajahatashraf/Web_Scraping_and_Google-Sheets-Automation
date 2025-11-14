import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os
import json

# ---------------- Google Sheets Setup ----------------
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not SERVICE_ACCOUNT_JSON:
    raise ValueError("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set")

SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_JSON)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def init_sheets_api(spreadsheet_id):
    """Initialize Google Sheets API from service account JSON in env variable."""
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    return service, sheet, spreadsheet_id

# ---------------- Merge Terminal CSVs ----------------
def update_terminal_sheet(sheet, spreadsheet_id, csv_file):
    data = pd.read_csv(csv_file)
    data['Terminal_Name'] = data['Terminal_Name'].astype(str).str.strip()

    TERMINAL_RANGE = 'NIGHT!H4:H'
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=TERMINAL_RANGE).execute()
    sheet_values = result.get('values', [])
    sheet_names = [row[0].strip() for row in sheet_values if row and row[0].strip()]

    update_body = []

    for idx, sheet_name in enumerate(sheet_names):
        match_row = data[data['Terminal_Name'] == sheet_name]
        if not match_row.empty:
            row_values = [
                int(match_row['Dispensed'].values[0]),
                int(match_row['SC_WDs'].values[0]),
                float(match_row['Load Amount'].values[0]),
                float(match_row['Cash_Balance'].values[0])
            ]
            update_body.append({
                'range': f'NIGHT!I{idx+4}:L{idx+4}',
                'values': [row_values]
            })
            print(f"✅ Terminal match found: {sheet_name}")
        else:
            print(f"❌ Terminal not found: {sheet_name}")

    return update_body

# ---------------- Update DeptSalesLog ----------------
def update_dept_sales(sheet, spreadsheet_id, dept_file, update_body):
    try:
        tables = pd.read_html(dept_file)
        dept_df = tables[0]
    except ValueError:
        dept_df = pd.read_excel(dept_file, skiprows=1)

    dept_df['Department'] = dept_df['Department'].astype(str).str.strip()
    dept_df['Net Sales'] = dept_df['Net Sales'].astype(str).str.replace(r'[^0-9.]', '', regex=True).astype(float)

    dept_range = 'NIGHT!D1:D'
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=dept_range).execute()
    sheet_depts = result.get('values', [])

    for row_idx, row in enumerate(sheet_depts):
        if not row:
            continue
        dept_name = str(row[0]).strip()
        match_row = dept_df[dept_df['Department'] == dept_name]
        if not match_row.empty:
            net_sales_value = float(match_row['Net Sales'].values[0])
            update_body.append({
                'range': f'NIGHT!E{row_idx + 1}',
                'values': [[net_sales_value]]
            })
            print(f"✅ Dept match updated: {dept_name} → {net_sales_value}")
        else:
            print(f"❌ Dept not found in Excel: {dept_name}")

    return update_body

# ---------------- Update BillPayReport ----------------
def update_billpay_totals(sheet, spreadsheet_id, bill_file, update_body):
    try:
        tables = pd.read_html(bill_file)
        bill_df = tables[0]
    except ValueError:
        bill_df = pd.read_excel(bill_file, skiprows=1)

    bill_df = bill_df.dropna(how='all')
    last_row_candidates = bill_df[['Taxes', 'Cash', 'Credit Cards', 'Total Out']].dropna(how='all')

    if last_row_candidates.empty:
        print("❌ No totals row found in BillPayReport.xls")
        return update_body

    last_row = last_row_candidates.iloc[-1]

    def clean_value(val):
        val = str(val).replace(',', '').replace('$', '').strip()
        if '(' in val and ')' in val:
            val = '-' + val.replace('(', '').replace(')', '')
        try:
            return float(val)
        except:
            return 0.0

    taxes_total = clean_value(last_row['Taxes'])
    cash_total = clean_value(last_row['Cash'])
    credit_total = clean_value(last_row['Credit Cards'])
    total_out = clean_value(last_row['Total Out'])

    update_body.extend([
        {'range': 'NIGHT!B9', 'values': [[taxes_total]]},
        {'range': 'NIGHT!B10', 'values': [[cash_total]]},
        {'range': 'NIGHT!B11', 'values': [[credit_total]]},
        {'range': 'NIGHT!B12', 'values': [[total_out]]},
    ])

    print(f"✅ BillPay totals updated from last row: Taxes={taxes_total}, Cash={cash_total}, Credit={credit_total}, Total Out={total_out}")
    return update_body

# ---------------- Batch update to Google Sheets ----------------
def batch_update_sheet(service, spreadsheet_id, update_body):
    if update_body:
        body = {
            'valueInputOption': 'RAW',
            'data': update_body
        }
        result = service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        print(f"✅ Updated {result.get('totalUpdatedCells')} cells successfully!")
    else:
        print("⚠️ No matched rows to update.")

# ---------------- Main function ----------------
def update_google_sheets(data_dir):
    spreadsheet_id = '1WO32B6cc49wri74yuRBkiGYTgvNz6ougIAOyxhG2bIk'

    service, sheet, spreadsheet_id = init_sheets_api(spreadsheet_id)
    update_body = []

    # 1️⃣ Terminal CSV
    terminal_csv = os.path.join(data_dir, 'merged_terminal_report.csv')
    update_body = update_terminal_sheet(sheet, spreadsheet_id, terminal_csv)

    # 2️⃣ DeptSalesLog
    # dept_file = os.path.join(data_dir, 'DeptSalesLog.xls')
    # update_body = update_dept_sales(sheet, spreadsheet_id, dept_file, update_body)
    #
    # # 3️⃣ BillPayReport
    # bill_file = os.path.join(data_dir, 'BillPayReport.xls')
    # update_body = update_billpay_totals(sheet, spreadsheet_id, bill_file, update_body)

    # 4️⃣ Batch update
    batch_update_sheet(service, spreadsheet_id, update_body)


if __name__ == "__main__":
    DATA_DIR = "./data"
    update_google_sheets(DATA_DIR)
