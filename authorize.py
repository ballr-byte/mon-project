"""
Run this script once to authorize Gmail access.
It will print a URL — open it in your browser, sign in with peakline.org@gmail.com,
then paste the authorization code back here.
"""

import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.pickle"

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

auth_url, _ = flow.authorization_url(prompt="consent")

print("\n--- STEP 1 ---")
print("Open this URL in your browser:\n")
print(auth_url)
print("\n--- STEP 2 ---")
code = input("Paste the authorization code here: ").strip()

flow.fetch_token(code=code)
creds = flow.credentials

with open(TOKEN_FILE, "wb") as f:
    pickle.dump(creds, f)

print("\nAuthorization successful! token.pickle saved.")
print("You can now run: python main.py all")
