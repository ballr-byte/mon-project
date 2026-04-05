"""
Scrapes Yelp for auto detailing businesses across US & Canada.
Uses requests + BeautifulSoup (no browser required).
"""

import csv
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

CITIES = [
    # USA
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX",
    "Phoenix, AZ", "Philadelphia, PA", "San Antonio, TX", "San Diego, CA",
    "Dallas, TX", "San Jose, CA", "Austin, TX", "Jacksonville, FL",
    "Fort Worth, TX", "Columbus, OH", "Charlotte, NC", "Indianapolis, IN",
    "San Francisco, CA", "Seattle, WA", "Denver, CO", "Nashville, TN",
    "Las Vegas, NV", "Portland, OR", "Atlanta, GA", "Miami, FL",
    # Canada
    "Toronto, ON", "Montreal, QC", "Vancouver, BC", "Calgary, AB",
    "Edmonton, AB", "Ottawa, ON", "Winnipeg, MB", "Hamilton, ON",
]

OUTPUT_FILE = "leads.csv"
MAX_PER_CITY = 5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_city(city: str) -> list[dict]:
    leads = []
    url = f"https://www.yelp.com/search?find_desc=auto+detailing&find_loc={quote(city)}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Find business result cards
        results = soup.select('h3 a[href*="/biz/"]')
        results = results[:MAX_PER_CITY]

        for link in results:
            name = link.get_text(strip=True)
            href = link.get("href", "")
            if not name or not href:
                continue

            full_url = f"https://www.yelp.com{href}" if href.startswith("/") else href

            # Visit business page to get website
            website = ""
            phone = ""
            address = ""
            try:
                biz_resp = requests.get(full_url, headers=HEADERS, timeout=12)
                biz_soup = BeautifulSoup(biz_resp.text, "html.parser")

                # Website
                website_link = biz_soup.find("a", href=re.compile(r"^https?://"), string=re.compile(r"\.", re.I))
                if not website_link:
                    website_link = biz_soup.find("a", {"href": re.compile(r"biz_redir")})
                if website_link:
                    website = website_link.get("href", "")
                    # Clean up Yelp redirect URLs
                    if "biz_redir" in website:
                        match = re.search(r"url=([^&]+)", website)
                        if match:
                            from urllib.parse import unquote
                            website = unquote(match.group(1))

                # Phone
                phone_el = biz_soup.find("p", string=re.compile(r"\(\d{3}\)"))
                if phone_el:
                    phone = phone_el.get_text(strip=True)

                # Address
                addr_el = biz_soup.find("address")
                if addr_el:
                    address = addr_el.get_text(separator=", ", strip=True)

                time.sleep(1)

            except Exception:
                pass

            leads.append({
                "business_name": name,
                "city": city,
                "address": address,
                "phone": phone,
                "website": website,
                "email": "",
                "status": "new",
            })
            print(f"  [+] {name} | {website or 'no website'}")

    except Exception as e:
        print(f"  [!] Error scraping {city}: {e}")

    return leads


def run_scraper():
    all_leads = []

    for city in CITIES:
        print(f"\nScraping: {city}")
        leads = scrape_city(city)
        all_leads.extend(leads)
        time.sleep(3)  # polite delay between cities

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
    run_scraper()
