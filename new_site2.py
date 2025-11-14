import time
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Credentials ---
USERNAME = "daveysdiscount"
PASSWORD = "London2525$"

# --- URLs ---
URL_GASSALES = "https://secure.cstorepro.com/EmagineNETCOSM/Content/POSManagement/POSReports/POSGasSales.aspx?&enetFoundationMenuID=1834"
URL_SALESREPORT = "https://secure.cstorepro.com/EmagineNETCOSM/Content/Reports/SalesReport.aspx?ShowAllStores=1&enetFoundationMenuID=1836"
URL_Departmentsale = "https://secure.cstorepro.com/EmagineNETCOSM/Content/POSManagement/POSReports/DeptSalesSummary.aspx?&enetFoundationMenuID=1840"
# --- Chrome setup ---
options = uc.ChromeOptions()
options.add_argument("--start-maximized")
# options.add_argument("--headless=new")  # Headless mode

# Set download directory
current_dir = os.getcwd()
prefs = {
    "download.default_directory": current_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

# Create driver
driver = uc.Chrome(options=options, version_main=141)
print("Download folder set to:", current_dir)

try:
    driver.get(URL_GASSALES)

    # --- Fill login fields ---
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "EWFLogin_Form_txtUserName"))
    ).send_keys(USERNAME)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "EWFLogin_Form_txtPassword"))
    ).send_keys(PASSWORD)
    print("Username and password filled. Waiting for CAPTCHA to be solved manually...")

    # --- Wait for CAPTCHA solved manually ---
    logged_in = False
    while not logged_in:
        try:
            token_input = driver.find_element(By.NAME, "cf-turnstile-response")
            token_value = token_input.get_attribute("value")
            if token_value and token_value.strip() != "":
                print("CAPTCHA solved! Clicking login button...")
                WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "EWFLoginBtn"))
                ).click()
                logged_in = True
            else:
                print("Waiting for CAPTCHA solution...")
        except Exception:
            pass
        time.sleep(10)

    print("Logged in successfully.")
    time.sleep(5)

    # --- GAS SALES REPORT ---
    main_datepicker = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "GasSalesLog_Form_ReportDate_EnetDRS"))
    )
    main_datepicker.click()
    time.sleep(1)

    driver.execute_script("""
    var start = document.querySelector('input[name="daterangepicker_start"]');
    var end = document.querySelector('input[name="daterangepicker_end"]');
    start.value = '11/11/2025';
    end.value = '11/13/2025';
    ['input','change','blur'].forEach(evt=>{
        start.dispatchEvent(new Event(evt, { bubbles: true }));
        end.dispatchEvent(new Event(evt, { bubbles: true }));
    });
    """)
    print("Gas Sales date range set.")

    apply_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.applyBtn.btn.btn-default.btn-small.btn-primary"))
    )
    apply_btn.click()
    print("Applied Gas Sales date range.")
    time.sleep(2)

    run_report_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "btnGasSalesLog_Filter_Search"))
    )
    run_report_btn.click()
    print("Running Gas Sales report...")
    time.sleep(5)

    download_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//i[contains(@class,'glyphicon-download-alt')]/parent::*"))
    )
    download_btn.click()
    print("Gas Sales file downloading to:", current_dir)

    # Wait for download to complete
    time.sleep(10)

    # -------------------------------------------------------------------
    # --- SALES REPORT ---
    # -------------------------------------------------------------------
    print("\nNavigating to Sales Report page...")
    driver.get(URL_SALESREPORT)

    # Wait for datepicker field
    date_input = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "BillPayReport_Form_reportDate_EnetDRS"))
    )
    date_input.click()
    time.sleep(1)

    driver.execute_script("""
    var start = document.querySelector('input[name="daterangepicker_start"]');
    var end = document.querySelector('input[name="daterangepicker_end"]');
    start.value = '11/11/2025';
    end.value = '11/13/2025';
    ['input','change','blur'].forEach(evt=>{
        start.dispatchEvent(new Event(evt, { bubbles: true }));
        end.dispatchEvent(new Event(evt, { bubbles: true }));
    });
    """)
    print("Sales Report date range set.")

    apply_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.applyBtn.btn.btn-default.btn-small.btn-primary"))
    )
    apply_btn.click()
    print("Applied Sales Report date range.")
    time.sleep(2)

    # --- Click 'Run report' ---
    run_report_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "btnBillPayReport_Filter_Search"))
    )
    run_report_btn.click()
    print("Run report clicked for Sales Report.")
    time.sleep(6)

    # --- Click 'Download' ---
    download_btn = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//i[contains(@class,'glyphicon-download-alt')]/parent::*"))
    )
    download_btn.click()
    print("Sales Report download started. File saving to:", current_dir)

    # Wait for file to complete download
    time.sleep(10)
    # -------------------------------------------------------------------
    # ---  Department SALES REPORT ---
    # -------------------------------------------------------------------
    print("\nNavigating to Sales Report page...")
    driver.get(URL_Departmentsale)

    # Wait for datepicker field
    date_input = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "DeptSalesLog_Form_ReportDate_EnetDRS"))
    )
    date_input.click()
    time.sleep(1)

    driver.execute_script("""
        var start = document.querySelector('input[name="daterangepicker_start"]');
        var end = document.querySelector('input[name="daterangepicker_end"]');
        start.value = '11/11/2025';
        end.value = '11/13/2025';
        ['input','change','blur'].forEach(evt=>{
            start.dispatchEvent(new Event(evt, { bubbles: true }));
            end.dispatchEvent(new Event(evt, { bubbles: true }));
        });
        """)
    print("Sales Report date range set.")

    apply_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.applyBtn.btn.btn-default.btn-small.btn-primary"))
    )
    apply_btn.click()
    print("Applied Sales Report date range.")
    time.sleep(2)

    # --- Click 'Run report' ---
    run_report_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "btnDeptSalesLog_Filter_Search"))
    )
    run_report_btn.click()
    print("Run report clicked for Sales Report.")
    time.sleep(6)

    # --- Click 'Download' ---
    download_btn = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//i[contains(@class,'glyphicon-download-alt')]/parent::*"))
    )
    download_btn.click()
    print("Sales Report download started. File saving to:", current_dir)

    # Wait for file to complete download
    time.sleep(10)

    print("\n✅ Both reports downloaded successfully!")
    print("Browser will remain open. Press Ctrl+C to close manually.")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Closing browser...")
    driver.quit()

finally:
    try:
        driver.quit()
    except Exception:
        pass
