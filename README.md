# Peakline Marketing — Cold Email Outreach

Automated pipeline: scrape auto detailing leads from Google Maps → find contact emails → send personalized cold emails via Gmail.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Set up Gmail API credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Go to **APIs & Services → Library** and enable the **Gmail API**
4. Go to **APIs & Services → Credentials**
5. Click **Create Credentials → OAuth 2.0 Client ID**
6. Application type: **Desktop app**
7. Download the JSON file and rename it to `credentials.json`
8. Place `credentials.json` in this project folder

> The first time you run `send`, a browser window will open asking you to authorize the app with your Gmail account. After that, a `token.pickle` file is saved so you won't need to authorize again.

---

## Usage

Run each step individually:

```bash
# Step 1 — Scrape auto detailing businesses from Google Maps
python main.py scrape

# Step 2 — Visit each website to find a contact email
python main.py find-emails

# Step 3 — Send cold emails (default: 50)
python main.py send

# Send a custom number
python main.py send --limit 25

# Run everything in one go
python main.py all
```

---

## Output

- `leads.csv` — all scraped leads with columns:
  - `business_name`, `city`, `address`, `phone`, `website`, `email`, `status`
  - `status` values: `new` → `sent` / `failed`

---

## Tips

- The sender waits **60 seconds between emails** to avoid Gmail spam filters. Sending 50 emails takes ~50 minutes.
- Keep daily sends under **100/day** on a regular Gmail account. Use Google Workspace for higher volume.
- You can edit the email subject/body in `sender.py` → `build_email()` function.
- To re-send failed emails, change their `status` back to `new` in `leads.csv`.
