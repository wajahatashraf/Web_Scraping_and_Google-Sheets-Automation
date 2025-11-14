import pandas as pd
import os

def merge_terminal_reports(data_dir):
    """
    Merge Terminal Activity Summary, Terminal Status Report, and Terminal Cash Balance
    into a single CSV file in the data folder.

    Args:
        data_dir (str): Path to the folder containing downloaded Excel files.

    Returns:
        str: Path to the merged CSV file.
    """
    # --- File paths ---
    activity_file = os.path.join(data_dir, "Terminal_Activity_Summary.xls")
    status_file = os.path.join(data_dir, "Terminal_Status_Report.xls")
    cash_file = os.path.join(data_dir, "wrptCashBalance.xls")
    output_file = os.path.join(data_dir, "merged_terminal_report.csv")

    def smart_read(file_path):
        """Try reading as HTML first, fall back to Excel."""
        try:
            df = pd.read_html(file_path)[0]
        except Exception:
            df = pd.read_excel(file_path, engine="xlrd")  # legacy .xls
        df.columns = df.columns.str.strip()  # normalize column names
        return df

    # --- 1. Read Terminal Activity Summary ---
    activity_df = smart_read(activity_file)
    activity_df = activity_df[['Terminal_Name', 'Dispensed', 'SC_WDs']]

    # --- 2. Read Terminal Status Report ---
    status_df = smart_read(status_file)
    status_df = status_df[['Name', 'Cash_Balance']]

    # --- 3. Read Terminal Cash Balance ---
    cash_df = pd.read_excel(cash_file, skiprows=3, engine="xlrd")
    cash_df = cash_df[cash_df['Terminal Location'].notna() & (cash_df['Terminal Location'] != 'Totals:')]
    cash_df = cash_df[['Terminal Location', 'Load Amount']]
    cash_df['Load Amount'] = cash_df['Load Amount'].astype(str)

    # --- 4. Merge Activity + Status ---
    merged_df = activity_df.merge(status_df, left_on='Terminal_Name', right_on='Name', how='left')
    merged_df = merged_df.drop(columns=['Name'])

    # --- 5. Merge with Cash Balance ---
    merged_df = merged_df.merge(cash_df, left_on='Terminal_Name', right_on='Terminal Location', how='left')
    merged_df = merged_df.drop(columns=['Terminal Location'])

    # --- 6. Save to CSV ---
    merged_df.to_csv(output_file, index=False)
    print(f"✅ Merged CSV saved to {output_file}")

    return output_file
