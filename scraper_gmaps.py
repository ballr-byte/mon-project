"""
Scrapes Google Maps for auto detailing businesses using Playwright.
Run this on your local Windows machine.
"""

import csv
import asyncio
import time
from playwright.async_api import async_playwright

CITIES = [
    "New York NY", "Los Angeles CA", "Chicago IL", "Houston TX",
    "Phoenix AZ", "San Diego CA", "Dallas TX", "Austin TX",
    "San Francisco CA", "Seattle WA", "Denver CO", "Nashville TN",
    "Las Vegas NV", "Portland OR", "Atlanta GA", "Miami FL",
    "Toronto ON", "Vancouver BC", "Calgary AB", "Montreal QC",
]

OUTPUT_FILE = "leads.csv"
MAX_PER_CITY = 5

async def scrape_city(page, city):
    leads = []
    query = f"auto detailing {city}"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

    try:
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(3000)

        # Scroll results to load more
        for _ in range(3):
            await page.keyboard.press("Tab")
            await page.wait_for_timeout(500)

        # Get all listing links
        listings = await page.locator('[role="feed"] a[href*="/maps/place/"]').all()
        listings = listings[:MAX_PER_CITY]

        for listing in listings:
            try:
                name = await listing.get_attribute("aria-label") or ""
                href = await listing.get_attribute("href") or ""
                if not name or not href:
                    continue

                # Open detail page
                detail = await page.context.new_page()
                await detail.goto(href, timeout=20000)
                await detail.wait_for_timeout(2000)

                # Website
                website = ""
                web_el = detail.locator('a[data-item-id="authority"]')
                if await web_el.count() > 0:
                    website = await web_el.get_attribute("href") or ""

                # Phone
                phone = ""
                phone_el = detail.locator('[data-item-id^="phone"]')
                if await phone_el.count() > 0:
                    phone = (await phone_el.get_attribute("aria-label") or "").replace("Phone:", "").strip()

                # Address
                address = ""
                addr_el = detail.locator('[data-item-id="address"]')
                if await addr_el.count() > 0:
                    address = (await addr_el.get_attribute("aria-label") or "").replace("Address:", "").strip()

                await detail.close()

                leads.append({
                    "business_name": name.strip(),
                    "city": city,
                    "address": address,
                    "phone": phone,
                    "website": website,
                    "email": "",
                    "status": "new",
                })
                print(f"  [+] {name.strip()} | {website or 'no website'}")

            except Exception as e:
                print(f"  [!] Listing error: {e}")
                try:
                    await detail.close()
                except:
                    pass

    except Exception as e:
        print(f"  [!] City error {city}: {e}")

    return leads


async def run_scraper():
    all_leads = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # visible browser
        context = await browser.new_context()
        page = await context.new_page()

        for city in CITIES:
            print(f"\nScraping: {city}")
            leads = await scrape_city(page, city)
            all_leads.extend(leads)
            time.sleep(2)

        await browser.close()

    if all_leads:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_leads[0].keys())
            writer.writeheader()
            writer.writerows(all_leads)
        print(f"\nSaved {len(all_leads)} leads to {OUTPUT_FILE}")
    else:
        print("\nNo leads found.")


if __name__ == "__main__":
    asyncio.run(run_scraper())
