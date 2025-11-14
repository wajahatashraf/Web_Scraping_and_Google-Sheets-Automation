import time
import asyncio
from playwright.async_api import async_playwright

USERNAME = "daveysdiscount"
PASSWORD = "London2525$"

URL_GASSALES = (
    "https://secure.cstorepro.com/EmagineNETCOSM/Content/"
    "POSManagement/POSReports/POSGasSales.aspx?&enetFoundationMenuID=1834"
)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # must be False in Python
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-infobars",
                "--window-size=1920,1080",
                "--window-position=-2000,-2000",  # hide browser off-screen
            ]
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1920, "height": 1080},
        )

        page = await context.new_page()
        print("Opening login page...")
        await page.goto(URL_GASSALES, wait_until="networkidle")

        # Fill username/password
        await page.fill("#EWFLogin_Form_txtUserName", USERNAME)
        await page.fill("#EWFLogin_Form_txtPassword", PASSWORD)

        print("Waiting for CAPTCHA...")

        async def click_human_checkbox():
            label_selector = "label.cb-lb:has-text('Verify you are human')"
            if await page.locator(label_selector).count() > 0:
                print("➡ Human verification checkbox found — clicking...")
                await page.locator(label_selector).click()
                await asyncio.sleep(2)
                return True
            return False

        captcha_solved = False
        while not captcha_solved:
            # click checkbox if present
            await click_human_checkbox()

            token_value = await page.evaluate("""
                () => {
                    let el = document.querySelector("input[name='cf-turnstile-response']");
                    return el ? el.value : "";
                }
            """)

            if token_value and token_value.strip() != "":
                print("🎉 CAPTCHA solved automatically!")
                captcha_solved = True
                break

            print("⏳ Waiting 3 seconds...")
            await asyncio.sleep(3)

        # Click login button
        print("Logging in...")
        await page.click("#EWFLoginBtn")
        await page.wait_for_load_state("networkidle")
        print("✅ Logged in successfully!")

        # Keep browser running invisible
        while True:
            await asyncio.sleep(2)

asyncio.run(main())
