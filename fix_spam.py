"""
Rewrites sender_detailing.py and sender_landscaping.py with:
- DAILY_LIMIT = 20
- DELAY = 120
- No booking link in email body
"""
import os

SENDER_TEMPLATE = '''import base64,csv,os,time,pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
LEADS_FILE=r"C:\\peakline\\leads_{niche}.csv"
CREDENTIALS_FILE=r"C:\\peakline\\credentials.json"
TOKEN_FILE=r"C:\\peakline\\token.pickle"
SCOPES=["https://www.googleapis.com/auth/gmail.send"]
SENDER_NAME="Peakline Marketing"
SENDER_EMAIL="peakline.org@gmail.com"
DAILY_LIMIT=20
DELAY=120
def build_email(name):
    subject=f"Quick question for {{name}}"
    body=f"""Hey {{name}},

Was checking out your website and noticed you still had some unbooked appointments. Quick question, are you getting consistent leads online or mostly word of mouth?

I help local service businesses get 20-30 qualified leads every month using paid ads — and you only pay when the leads actually come in.

Worth a quick 10 min call? Just reply to this email and we can set something up.

Best,
Peakline Marketing"""
    return subject,body
def get_service():
    creds=None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE,"rb") as f: creds=pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        else:
            flow=InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE,SCOPES)
            creds=flow.run_local_server(port=0)
        with open(TOKEN_FILE,"wb") as f: pickle.dump(creds,f)
    return build("gmail","v1",credentials=creds)
def send_email(service,to,name):
    subject,body=build_email(name)
    msg=MIMEMultipart("alternative")
    msg["to"]=to; msg["subject"]=subject; msg["from"]=f"{{SENDER_NAME}} <{{SENDER_EMAIL}}>"
    msg.attach(MIMEText(body,"plain"))
    raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
    try: service.users().messages().send(userId="me",body={{"raw":raw}}).execute(); return True
    except HttpError as e: print(f"    [!] {{e}}"); return False
def run_sender(limit=DAILY_LIMIT):
    service=get_service()
    with open(LEADS_FILE,"r",encoding="utf-8") as f: leads=list(csv.DictReader(f))
    pending=[l for l in leads if l.get("email") and l.get("status")=="new"][:limit]
    if not pending: print("No pending leads."); return
    print(f"Sending to {{len(pending)}} leads...\\n")
    sent=0
    for i,lead in enumerate(pending):
        print(f"[{{i+1}}/{{len(pending)}}] {{lead[\'business_name\']}} <{{lead[\'email\']}}>")
        if send_email(service,lead["email"],lead["business_name"]):
            lead["status"]="sent"; sent+=1; print("    Sent!")
        else: lead["status"]="failed"; print("    Failed.")
        with open(LEADS_FILE,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=leads[0].keys()); w.writeheader(); w.writerows(leads)
        if i<len(pending)-1: print(f"    Waiting {{DELAY}}s..."); time.sleep(DELAY)
    print(f"\\nDone. Sent {{sent}}/{{len(pending)}} emails.")
if __name__=="__main__": run_sender()
'''

for niche in ["detailing", "landscaping"]:
    path = rf"C:\peakline\sender_{niche}.py"
    with open(path, "w", encoding="utf-8") as f:
        f.write(SENDER_TEMPLATE.format(niche=niche))
    print(f"Updated sender_{niche}.py")

print("\nDone! Changes applied:")
print("- Daily limit: 20 emails per run")
print("- Delay: 120 seconds between emails")
print("- No booking link in email (reply-based instead)")
