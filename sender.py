"""
Sends personalized cold emails via Gmail API to leads from leads.csv.
Marks each lead as 'sent' or 'failed' in the CSV after attempting.
"""

import base64
import csv
import os
import time
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

LEADS_FILE = "leads.csv"
CREDENTIALS_FILE = "credentials.json"  # downloaded from Google Cloud Console
TOKEN_FILE = "token.pickle"

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

SENDER_NAME = "Peakline Marketing"
DAILY_LIMIT = 50          # max emails per run
DELAY_BETWEEN_EMAILS = 60  # seconds between sends (avoids spam flags)

# ---------------------------------------------------------------------------
# Email template — customize subject/body below
# ---------------------------------------------------------------------------

def build_email(business_name: str) -> tuple[str, str]:
    """Returns (subject, body) for a given business name."""

    subject = f"Quick question for {business_name}"

    body = f"""Hey {business_name},

Was checking out your website and noticed you still had some unbooked appointments. I help local based service businesses generate 20-30 qualified leads in a 30 day period on a pay for performance basis using Facebook ads — you only pay when the ads actually bring in leads. Literally no risk, just results.

If you're open for a quick 10-15 min live call, I could show you how this works.

Best,
Peakline Marketing"""

    return subject, body


# ---------------------------------------------------------------------------
# Gmail auth
# ---------------------------------------------------------------------------

def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"'{CREDENTIALS_FILE}' not found.\n"
                    "Please follow the setup instructions in README.md to download "
                    "your Gmail API credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("gmail", "v1", credentials=creds)


# ---------------------------------------------------------------------------
# Send a single email
# ---------------------------------------------------------------------------

def send_email(service, to_email: str, business_name: str) -> bool:
    subject, body = build_email(business_name)

    message = MIMEMultipart("alternative")
    message["to"] = to_email
    message["subject"] = subject
    message["from"] = SENDER_NAME

    message.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()
        return True
    except HttpError as e:
        print(f"    [!] Gmail API error: {e}")
        return False


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_sender(limit: int = DAILY_LIMIT):
    service = get_gmail_service()

    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        leads = list(csv.DictReader(f))

    # Only send to leads with an email that haven't been contacted yet
    pending = [l for l in leads if l.get("email") and l.get("status") == "new"]

    if not pending:
        print("No pending leads with emails found. Run email_finder.py first.")
        return

    to_send = pending[:limit]
    print(f"Sending emails to {len(to_send)} leads (limit: {limit})...\n")

    sent_count = 0
    for i, lead in enumerate(to_send):
        name = lead["business_name"]
        email = lead["email"]
        print(f"[{i+1}/{len(to_send)}] Sending to {name} <{email}>")

        success = send_email(service, email, name)

        if success:
            lead["status"] = "sent"
            sent_count += 1
            print(f"    Sent!")
        else:
            lead["status"] = "failed"
            print(f"    Failed.")

        # Write progress after each send so we don't lose state on crash
        with open(LEADS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=leads[0].keys())
            writer.writeheader()
            writer.writerows(leads)

        if i < len(to_send) - 1:
            print(f"    Waiting {DELAY_BETWEEN_EMAILS}s before next send...")
            time.sleep(DELAY_BETWEEN_EMAILS)

    print(f"\nDone. Sent {sent_count}/{len(to_send)} emails.")


if __name__ == "__main__":
    run_sender()
