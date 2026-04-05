"""
Google Maps scraper for auto detailing businesses across US & Canada.
Uses Playwright to search Google Maps and extract business info.
"""

import asyncio
import csv
import re
import time
from playwright.async_api import async_playwright

CITIES = [
    # USA
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX",
    "Phoenix, AZ", "Philadelphia, PA", "San Antonio, TX", "San Diego, CA",
    "Dallas, TX", "San Jose, CA", "Austin, TX", "Jacksonville, FL",
    "Fort Worth, TX", "Columbus, OH", "Charlotte, NC", "Indianapolis, IN",
    "San Francisco, CA", "Seattle, WA", "Denver, CO", "Nashville, TN",
    "Oklahoma City, OK", "Las Vegas, NV", "Portland, OR", "Memphis, TN",
    "Louisville, KY", "Baltimore, MD", "Milwaukee, WI", "Albuquerque, NM",
    "Tucson, AZ", "Fresno, CA", "Atlanta, GA", "Miami, FL",
    # Canada
    "Toronto, ON", "Montreal, QC", "Vancouver, BC", "Calgary, AB",
    "Edmonton, AB", "Ottawa, ON", "Winnipeg, MB", "Quebec City, QC",
    "Hamilton, ON", "Brampton, ON", "Surrey, BC", "Kitchener, ON",
]

SEARCH_QUERY = "auto detailing"
OUTPUT_FILE = "leads.csv"
MAX_PER_CITY = 5  # businesses to scrape per city (5 x 32 cities = ~160 leads)


async def scrape_city(page, city: str) -> list[dict]:
    leads = []
    query = f"{SEARCH_QUERY} {city}"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)

        # Scroll the results panel to load more listings
        results_panel = page.locator('[role="feed"]')
        for _ in range(3):
            await results_panel.evaluate("el => el.scrollBy(0, 500)")
            await page.wait_for_timeout(1000)

        # Collect all listing links
        listings = await page.locator('[role="feed"] a[href*="/maps/place/"]').all()
        listings = listings[:MAX_PER_CITY]

        for listing in listings:
            try:
                name = await listing.get_attribute("aria-label") or ""
                href = await listing.get_attribute("href") or ""
                if not name or not href:
                    continue

                # Open the listing detail page
                detail_page = await page.context.new_page()
                await detail_page.goto(href, wait_until="networkidle", timeout=20000)
                await detail_page.wait_for_timeout(2000)

                # Extract website
                website = ""
                website_link = detail_page.locator('a[data-item-id="authority"]')
                if await website_link.count() > 0:
                    website = await website_link.get_attribute("href") or ""

                # Extract phone
                phone = ""
                phone_el = detail_page.locator('[data-item-id^="phone"]')
                if await phone_el.count() > 0:
                    phone = await phone_el.get_attribute("aria-label") or ""
                    phone = phone.replace("Phone:", "").strip()

                # Extract address
                address = ""
                addr_el = detail_page.locator('[data-item-id="address"]')
                if await addr_el.count() > 0:
                    address = await addr_el.get_attribute("aria-label") or ""
                    address = address.replace("Address:", "").strip()

                if name:
                    leads.append({
                        "business_name": name.strip(),
                        "city": city,
                        "address": address,
                        "phone": phone,
                        "website": website,
                        "email": "",  # filled by email_finder.py
                        "status": "new",
                    })
                    print(f"  [+] {name.strip()} | {website or 'no website'}")

                await detail_page.close()

            except Exception as e:
                print(f"  [!] Error parsing listing: {e}")
                continue

    except Exception as e:
        print(f"  [!] Error scraping {city}: {e}")

    return leads


async def run_scraper():
    all_leads = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        for city in CITIES:
            print(f"\nScraping: {city}")
            leads = await scrape_city(page, city)
            all_leads.extend(leads)
            time.sleep(2)  # polite delay between cities

        await browser.close()

    # Save to CSV
    if all_leads:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_leads[0].keys())
            writer.writeheader()
            writer.writerows(all_leads)
        print(f"\nSaved {len(all_leads)} leads to {OUTPUT_FILE}")
    else:
        print("\nNo leads found.")

    return all_leads


if __name__ == "__main__":
    asyncio.run(run_scraper())
