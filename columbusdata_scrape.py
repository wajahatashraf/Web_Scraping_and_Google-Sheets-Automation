import asyncio
import os
from pathlib import Path
from clean_data import merge_terminal_reports
import config
from playwright.async_api import async_playwright

# ---------------------- Constants ----------------------
DATA_DIR = Path(os.getcwd()) / "data"
DATA_DIR.mkdir(exist_ok=True)

# ---------------------- Utility Functions ----------------------
async def wait_for_selector(frame, selector, description="", clickable=False, timeout=20000):
    try:
        if clickable:
            element = await frame.wait_for_selector(selector, state="visible", timeout=timeout)
        else:
            element = await frame.wait_for_selector(selector, timeout=timeout)
        print(f"✅ {description} loaded.")
        return element
    except Exception:
        raise Exception(f"❌ Timeout waiting for {description}: {selector}")

async def login(page):
    await page.goto(config.COLUMBUSDATA_URL)
    print("✅ Website loaded.")

    username_box = await wait_for_selector(page, "#UsernameTextbox", "Username textbox")
    await username_box.fill(config.COLUMBUSDATA_USERNAME)

    password_box = await wait_for_selector(page, "#PasswordTextbox", "Password textbox")
    await password_box.fill(config.COLUMBUSDATA_PASSWORD)

    login_button = await wait_for_selector(page, "#LoginButton", "Login button", clickable=True)
    await login_button.click()
    print("✅ Login button clicked...")
    await page.wait_for_timeout(5000)

async def hover_and_click_quick_view(page, link_title):
    quick_view_button = await wait_for_selector(page, "//span[contains(@class,'rmText') and text()='Quick View']", "Quick View button")
    await quick_view_button.hover()
    print(f"✅ Hovered over 'Quick View' button for '{link_title}'")
    await page.wait_for_timeout(1000)

    for _ in range(3):
        try:
            target_link = await wait_for_selector(page, f"//a[contains(@title,'{link_title}')]", f"'{link_title}' link", clickable=True)
            await target_link.hover()
            await target_link.click()
            print(f"✅ Clicked '{link_title}' link")

            # Switch to the frame
            frame = page.frame(name="main")
            if not frame:
                raise Exception("❌ Frame 'main' not found")
            print("✅ Switched to frame 'main'")
            return frame
        except Exception as e:
            print(f"⚠️ Retry for '{link_title}' link: {e}")
            await page.wait_for_timeout(2000)
    raise Exception(f"❌ Failed to click '{link_title}' link after 3 attempts")

async def download_excel(page, frame):
    async with page.expect_download() as download_info:
        export_link = await wait_for_selector(frame, "#lnkExportExcel", "Export to Excel link", clickable=True)
        await export_link.scroll_into_view_if_needed()
        await export_link.click()
    download = await download_info.value
    download_path = DATA_DIR / download.suggested_filename
    await download.save_as(download_path)
    print(f"✅ File downloaded: {download_path}")
    return download_path

async def scrape_terminal_cash_balance(page):
    try:
        reports_menu = await wait_for_selector(page, "//span[text()='Reports']", "Reports menu")
        await reports_menu.hover()
        print("✅ Hovered over 'Reports' menu")
        await page.wait_for_timeout(1000)

        terminal_reports = await wait_for_selector(page, "//span[contains(@class,'rmText') and text()='Terminal Reports']", "Terminal Reports submenu")
        await terminal_reports.hover()
        print("✅ Hovered over 'Terminal Reports' submenu")
        await page.wait_for_timeout(1000)

        cash_balance_link = await wait_for_selector(page, "//a[span[text()='Terminal Cash Balance Rpt']]", "Terminal Cash Balance link", clickable=True)
        await cash_balance_link.scroll_into_view_if_needed()
        await cash_balance_link.click()
        print("✅ Clicked 'Terminal Cash Balance Rpt' link")

        frame = page.frame(name="main")
        if not frame:
            raise Exception("❌ Frame 'main' not found for cash balance report")

        # Select MS Excel
        format_dropdown = await wait_for_selector(frame, "#ddlReportFormat_Input", "Report Format dropdown", clickable=True)
        await format_dropdown.click()
        ms_excel_option = await wait_for_selector(frame, "//li[text()='MS Excel']", "MS Excel option", clickable=True)
        await ms_excel_option.click()
        print("✅ Selected MS Excel format")

        view_button = await wait_for_selector(frame, "#btnView", "View Report button", clickable=True)
        async with page.expect_download() as download_info:
            await view_button.click()
        download = await download_info.value
        download_path = DATA_DIR / download.suggested_filename
        await download.save_as(download_path)
        print(f"✅ 'Terminal Cash Balance Rpt' downloaded: {download_path}")
        return download_path

    except Exception as e:
        print(f"❌ Error scraping Terminal Cash Balance: {e}")

# ---------------------- Main Scraper ----------------------
async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        await login(page)

        # Terminal Transaction Summary
        frame1 = await hover_and_click_quick_view(page, "Terminal Transaction Summary")
        await download_excel(page, frame1)

        # Terminal Status Info
        frame2 = await hover_and_click_quick_view(page, "Terminal Status Info")
        await download_excel(page, frame2)

        # Terminal Cash Balance
        await scrape_terminal_cash_balance(page)

        # Merge CSVs
        merged_csv = merge_terminal_reports(DATA_DIR)
        print(f"🔹 Merging done. Output file: {merged_csv}")

        await browser.close()
        print("✅ Browser closed")

# ---------------------- Run ----------------------
if __name__ == "__main__":
    asyncio.run(run_scraper())
