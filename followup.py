import base64,csv,os,time,pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
LEADS_FILE=r"C:\peakline\leads.csv"
CREDENTIALS_FILE=r"C:\peakline\credentials.json"
TOKEN_FILE=r"C:\peakline\token.pickle"
SCOPES=["https://www.googleapis.com/auth/gmail.send"]
SENDER_NAME="Peakline Marketing"
SENDER_EMAIL="peakline.org@gmail.com"
DAILY_LIMIT=50
DELAY=60
def build_email(name):
    subject=f"Re: Quick question for {name}"
    body=f"""Hey {name},

Just wanted to follow up on my last email. Did you get a chance to check it out?

Still happy to jump on a quick 10 min call to show you how we get local service businesses 20-30 new leads a month.

Book here: https://lustrous-lollipop-5cd993.netlify.app/

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
    msg["to"]=to; msg["subject"]=subject; msg["from"]=f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg.attach(MIMEText(body,"plain"))
    raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
    try: service.users().messages().send(userId="me",body={"raw":raw}).execute(); return True
    except HttpError as e: print(f"    [!] {e}"); return False
def run_followup(limit=DAILY_LIMIT):
    service=get_service()
    with open(LEADS_FILE,"r",encoding="utf-8") as f: leads=list(csv.DictReader(f))
    pending=[l for l in leads if l.get("email") and l.get("status")=="sent"][:limit]
    if not pending: print("No leads to follow up with."); return
    print(f"Sending follow-ups to {len(pending)} leads...\n")
    sent=0
    for i,lead in enumerate(pending):
        print(f"[{i+1}/{len(pending)}] {lead['business_name']} <{lead['email']}>")
        if send_email(service,lead["email"],lead["business_name"]):
            lead["status"]="followup_sent"; sent+=1; print("    Sent!")
        else: lead["status"]="followup_failed"; print("    Failed.")
        with open(LEADS_FILE,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=leads[0].keys()); w.writeheader(); w.writerows(leads)
        if i<len(pending)-1: print(f"    Waiting {DELAY}s..."); time.sleep(DELAY)
    print(f"\nDone. Sent {sent}/{len(pending)} follow-ups.")
if __name__=="__main__": run_followup()
