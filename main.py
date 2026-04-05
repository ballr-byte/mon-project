"""
Main pipeline: scrape leads → find emails → send cold emails.
Run each step individually or run all at once.

Usage:
    python main.py scrape       # Step 1: Scrape Google Maps
    python main.py find-emails  # Step 2: Find contact emails from websites
    python main.py send         # Step 3: Send cold emails (default: 50)
    python main.py send --limit 25  # Send only 25 emails
    python main.py all          # Run all 3 steps in sequence
"""

import sys
import asyncio


def main():
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        return

    command = args[0]

    if command == "scrape":
        from scraper import run_scraper
        run_scraper()

    elif command == "find-emails":
        from email_finder import run_email_finder
        run_email_finder()

    elif command == "send":
        limit = 50
        if "--limit" in args:
            try:
                limit = int(args[args.index("--limit") + 1])
            except (IndexError, ValueError):
                print("Invalid --limit value, using default 50.")
        from sender import run_sender
        run_sender(limit=limit)

    elif command == "all":
        print("=== Step 1: Scraping Yelp ===")
        from scraper import run_scraper
        run_scraper()

        print("\n=== Step 2: Finding Emails ===")
        from email_finder import run_email_finder
        run_email_finder()

        print("\n=== Step 3: Sending Emails ===")
        from sender import run_sender
        run_sender()

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
