import time
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import csv
import config
import importlib
from clean_data import merge_terminal_reports



# --- Chrome Setup ---
CHROME_VERSION_MAIN = 141  # Match your installed Chrome version

# --- Create ./data folder ---
DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)

options = uc.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-popup-blocking")
options.add_argument("--window-size=1920,1080")
options.add_argument("--remote-debugging-port=9222")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

prefs = {
    "download.default_directory": DATA_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

# ---------------------- Utility Functions ----------------------
def init_driver():
    driver = uc.Chrome(
        version_main=CHROME_VERSION_MAIN,
        options=options,
        driver_executable_path=None,
        timeout=240,
    )
    driver.set_page_load_timeout(180)
    driver.set_script_timeout(180)
    wait = WebDriverWait(driver, 120)
    return driver, wait

def wait_for_element(driver, wait, by, locator, description="", clickable=False, retries=3):
    for attempt in range(retries):
        try:
            if clickable:
                element = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((by, locator))
                )
            else:
                element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((by, locator))
                )
            print(f"✅ {description} loaded.")
            return element
        except TimeoutException:
            print(f"⚠️ Timeout waiting for {description}, attempt {attempt + 1}/{retries}")
            time.sleep(2)
    raise TimeoutException(f"❌ Could not load {description} after {retries} attempts")

def login(driver, wait, username, password, url):
    driver.get(url)
    print("✅ Website loaded.")

    username_box = wait_for_element(driver, wait, By.ID, "UsernameTextbox", "Username textbox")
    username_box.clear()
    username_box.send_keys(username)

    password_box = wait_for_element(driver, wait, By.ID, "PasswordTextbox", "Password textbox")
    password_box.clear()
    password_box.send_keys(password)

    login_button = wait_for_element(driver, wait, By.ID, "LoginButton", "Login button", clickable=True)
    login_button.click()
    print("✅ Login button clicked...")
    time.sleep(5)

def hover_and_click_quick_view(driver, wait, link_title):
    quick_view_button = wait_for_element(
        driver, wait, By.XPATH, "//span[contains(@class,'rmText') and text()='Quick View']",
        "Quick View button"
    )
    ActionChains(driver).move_to_element(quick_view_button).perform()
    print(f"✅ Hovered over 'Quick View' button for '{link_title}'")
    time.sleep(1)

    for attempt in range(3):
        try:
            target_link = wait_for_element(
                driver, wait, By.XPATH, f"//a[contains(@title,'{link_title}')]",
                f"'{link_title}' link", clickable=True
            )
            ActionChains(driver).move_to_element(target_link).click().perform()
            print(f"✅ Clicked '{link_title}' link")
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
            print("✅ Switched to frame 'main'")
            return
        except Exception:
            print(f"⚠️ Retry {attempt + 1} for '{link_title}' link")
            time.sleep(2)
    raise Exception(f"❌ Failed to click '{link_title}' link after 3 attempts")

def download_excel(driver, wait):
    export_link = wait_for_element(driver, wait, By.ID, "lnkExportExcel", "Export to Excel link", clickable=True)
    driver.execute_script("arguments[0].scrollIntoView(true);", export_link)
    time.sleep(0.5)
    export_link.click()
    print(f"✅ Clicked 'Export to Excel'. File should download to {DATA_DIR}")
    time.sleep(5)

def scrape_terminal_cash_balance(driver, wait):
    try:
        reports_menu = wait.until(EC.visibility_of_element_located((By.XPATH, "//span[text()='Reports']")))
        ActionChains(driver).move_to_element(reports_menu).perform()
        print("✅ Hovered over 'Reports' menu.")
        time.sleep(1)

        terminal_reports = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//span[contains(@class,'rmText') and text()='Terminal Reports']")))
        ActionChains(driver).move_to_element(terminal_reports).perform()
        print("✅ Hovered over 'Terminal Reports' submenu.")
        time.sleep(1)

        cash_balance_link = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[span[text()='Terminal Cash Balance Rpt']]")))
        driver.execute_script("arguments[0].scrollIntoView(true);", cash_balance_link)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", cash_balance_link)
        print("✅ Clicked 'Terminal Cash Balance Rpt' link.")

        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))

        format_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "ddlReportFormat_Input")))
        format_dropdown.click()
        print("✅ Opened 'Report Format' dropdown.")

        ms_excel_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[text()='MS Excel']")))
        ms_excel_option.click()
        print("✅ Selected 'MS Excel' as report format.")

        view_button = wait.until(EC.element_to_be_clickable((By.ID, "btnView")))
        view_button.click()
        print("✅ Clicked 'View Report' button (MS Excel selected).")

        time.sleep(10)
        print(f"✅ 'Terminal Cash Balance Rpt' should now be downloading to {DATA_DIR}")

        driver.switch_to.default_content()
        print("✅ Returned to main dashboard.")

    except Exception as e:
        print(f"❌ Error scraping Terminal Cash Balance: {e}")

def run_scraper():
    driver, wait = init_driver()
    try:
        importlib.reload(config)
        # ---------------------- Credentials & URL ----------------------
        USERNAME = config.COLUMBUSDATA_USERNAME
        PASSWORD = config.COLUMBUSDATA_PASSWORD
        LOGIN_URL = config.COLUMBUSDATA_URL

        login(driver, wait, USERNAME, PASSWORD, LOGIN_URL)

        hover_and_click_quick_view(driver, wait, "Terminal Transaction Summary")
        download_excel(driver, wait)
        driver.switch_to.default_content()

        hover_and_click_quick_view(driver, wait, "Terminal Status Info")
        download_excel(driver, wait)
        driver.switch_to.default_content()

        scrape_terminal_cash_balance(driver, wait)

        merged_csv = merge_terminal_reports(DATA_DIR)
        print(f"🔹 Merging done. Output file: {merged_csv}")

    except Exception as e:
        print("❌ Error:", e)
    finally:
        driver.quit()
        print("✅ Browser closed")


if __name__ == "__main__":
    run_scraper()
