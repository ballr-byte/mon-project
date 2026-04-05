"""
Visits each business website from leads.csv and tries to find a contact email.
Updates the 'email' column in leads.csv.
"""

import csv
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
LEADS_FILE = "leads.csv"

# Pages most likely to have a contact email
CONTACT_PATHS = [
    "/contact", "/contact-us", "/contactus",
    "/about", "/about-us",
    "/reach-us", "/get-in-touch",
    "/info",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

SKIP_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "example.com", "domain.com", "email.com",
}

SKIP_PREFIXES = ("noreply", "no-reply", "donotreply", "support@", "info@wix", "info@squarespace")


def is_valid_email(email: str) -> bool:
    domain = email.split("@")[-1].lower()
    if domain in SKIP_DOMAINS:
        return False
    if any(email.lower().startswith(p) for p in SKIP_PREFIXES):
        return False
    return True


def extract_emails_from_html(html: str) -> list[str]:
    emails = EMAIL_REGEX.findall(html)
    return [e for e in emails if is_valid_email(e)]


def find_email_for_website(website: str) -> str:
    if not website:
        return ""

    # Normalize URL
    if not website.startswith("http"):
        website = "https://" + website

    found_emails = []

    try:
        # 1. Try homepage
        resp = requests.get(website, headers=HEADERS, timeout=10)
        emails = extract_emails_from_html(resp.text)
        found_emails.extend(emails)

        if not found_emails:
            # 2. Try common contact pages
            base = f"{urlparse(website).scheme}://{urlparse(website).netloc}"
            soup = BeautifulSoup(resp.text, "html.parser")

            # Look for contact links on homepage
            contact_links = []
            for a in soup.find_all("a", href=True):
                href = a["href"].lower()
                if any(p in href for p in ["contact", "about", "reach", "touch"]):
                    full = urljoin(base, a["href"])
                    if urlparse(full).netloc == urlparse(base).netloc:
                        contact_links.append(full)

            # Also try hardcoded paths
            for path in CONTACT_PATHS:
                contact_links.append(base + path)

            # Deduplicate
            contact_links = list(dict.fromkeys(contact_links))[:5]

            for link in contact_links:
                try:
                    r = requests.get(link, headers=HEADERS, timeout=8)
                    emails = extract_emails_from_html(r.text)
                    found_emails.extend(emails)
                    if found_emails:
                        break
                    time.sleep(0.5)
                except Exception:
                    continue

    except Exception as e:
        print(f"    [!] Could not fetch {website}: {e}")
        return ""

    # Return the first unique valid email
    seen = []
    for e in found_emails:
        if e.lower() not in [x.lower() for x in seen]:
            seen.append(e)

    return seen[0] if seen else ""


def run_email_finder():
    # Read leads
    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        leads = list(csv.DictReader(f))

    updated = 0
    for i, lead in enumerate(leads):
        if lead.get("email"):  # already has email, skip
            continue
        if not lead.get("website"):
            print(f"[{i+1}/{len(leads)}] {lead['business_name']} — no website, skipping")
            continue

        print(f"[{i+1}/{len(leads)}] {lead['business_name']} — {lead['website']}")
        email = find_email_for_website(lead["website"])
        if email:
            lead["email"] = email
            updated += 1
            print(f"    Found: {email}")
        else:
            print(f"    No email found")

        time.sleep(1)  # polite delay

    # Write back
    with open(LEADS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=leads[0].keys())
        writer.writeheader()
        writer.writerows(leads)

    print(f"\nDone. Found emails for {updated} leads.")


if __name__ == "__main__":
    run_email_finder()
