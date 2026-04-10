"""
Setup script - creates all detailing and landscaping files.
Run: python setup2.py
"""
import os

CITIES = """[
    "New York NY","Los Angeles CA","Chicago IL","Houston TX","Phoenix AZ",
    "Philadelphia PA","San Antonio TX","San Diego CA","Dallas TX","San Jose CA",
    "Austin TX","Jacksonville FL","Fort Worth TX","Columbus OH","Charlotte NC",
    "Indianapolis IN","San Francisco CA","Seattle WA","Denver CO","Nashville TN",
    "Oklahoma City OK","Las Vegas NV","Portland OR","Memphis TN","Louisville KY",
    "Baltimore MD","Milwaukee WI","Albuquerque NM","Tucson AZ","Fresno CA",
    "Atlanta GA","Miami FL","Sacramento CA","Kansas City MO","Omaha NE",
    "Raleigh NC","Colorado Springs CO","Virginia Beach VA","Minneapolis MN",
    "Tampa FL","New Orleans LA","Arlington TX","Bakersfield CA","Anaheim CA",
    "Aurora CO","Corpus Christi TX","Riverside CA","Lexington KY","St Louis MO",
    "Pittsburgh PA","Stockton CA","Cincinnati OH","St Paul MN","Toledo OH",
    "Greensboro NC","Newark NJ","Plano TX","Henderson NV","Lincoln NE",
    "Buffalo NY","Fort Wayne IN","Jersey City NJ","Orlando FL","Norfolk VA",
    "Chandler AZ","Laredo TX","Madison WI","Durham NC","Lubbock TX",
    "Winston Salem NC","Garland TX","Glendale AZ","Hialeah FL","Reno NV",
    "Baton Rouge LA","Irvine CA","Chesapeake VA","Irving TX","Scottsdale AZ",
    "Fremont CA","Gilbert AZ","San Bernardino CA","Birmingham AL",
    "Rochester NY","Richmond VA","Spokane WA","Des Moines IA","Montgomery AL",
    "Modesto CA","Fayetteville NC","Tacoma WA","Shreveport LA","Akron OH",
    "Aurora IL","Yonkers NY","Little Rock AR","Chattanooga TN",
    "Fort Lauderdale FL","Knoxville TN","Worcester MA",
    "Brownsville TX","Newport News VA","Salt Lake City UT","Tallahassee FL",
    "Huntsville AL","Grand Rapids MI","Tempe AZ","Cape Coral FL",
    "Overland Park KS","Jackson MS","Springfield MO","Ontario CA",
    "Toronto ON","Montreal QC","Vancouver BC","Calgary AB","Edmonton AB",
    "Ottawa ON","Winnipeg MB","Quebec City QC","Hamilton ON","Kitchener ON",
    "London ON","Victoria BC","Halifax NS","Oshawa ON","Windsor ON",
    "Saskatoon SK","Regina SK","Kelowna BC","Barrie ON","Abbotsford BC",
    "Sudbury ON","Kingston ON","Guelph ON","Moncton NB","Brantford ON",
    "Thunder Bay ON","Nanaimo BC","Burnaby BC","Surrey BC","Mississauga ON",
    "Brampton ON","Markham ON","Vaughan ON","Laval QC","Gatineau QC","Longueuil QC",
]"""

SCRAPER_TEMPLATE = '''import csv,asyncio,time
from playwright.async_api import async_playwright
CITIES={cities}
OUTPUT_FILE=r"C:\\peakline\\leads_{niche}.csv"
SEARCH="{search}"
MAX_PER_CITY=5
async def scrape_city(page,city):
    leads=[]
    url=f"https://www.google.com/maps/search/{{SEARCH.replace(' ','+')}}+{{city.replace(' ','+')}}"
    try:
        await page.goto(url,timeout=30000)
        await page.wait_for_timeout(3000)
        listings=await page.locator(\'[role="feed"] a[href*="/maps/place/"]\').all()
        for listing in listings[:MAX_PER_CITY]:
            try:
                name=await listing.get_attribute("aria-label") or ""
                href=await listing.get_attribute("href") or ""
                if not name or not href: continue
                detail=await page.context.new_page()
                await detail.goto(href,timeout=20000)
                await detail.wait_for_timeout(2000)
                website=phone=address=""
                wel=detail.locator(\'a[data-item-id="authority"]\')
                if await wel.count()>0: website=await wel.get_attribute("href") or ""
                pel=detail.locator(\'[data-item-id^="phone"]\')
                if await pel.count()>0: phone=(await pel.get_attribute("aria-label") or "").replace("Phone:","").strip()
                ael=detail.locator(\'[data-item-id="address"]\')
                if await ael.count()>0: address=(await ael.get_attribute("aria-label") or "").replace("Address:","").strip()
                await detail.close()
                leads.append({{"business_name":name.strip(),"city":city,"address":address,"phone":phone,"website":website,"email":"","status":"new"}})
                print(f"  [+] {{name.strip()}} | {{website or \'no website\'}}")
            except:
                try: await detail.close()
                except: pass
    except Exception as e: print(f"  [!] {{e}}")
    return leads
async def run_scraper():
    all_leads=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=False)
        context=await browser.new_context()
        page=await context.new_page()
        for city in CITIES:
            print(f"\\nScraping: {{city}}")
            all_leads.extend(await scrape_city(page,city))
            time.sleep(2)
        await browser.close()
    if all_leads:
        with open(OUTPUT_FILE,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=all_leads[0].keys())
            w.writeheader(); w.writerows(all_leads)
        print(f"\\nSaved {{len(all_leads)}} leads to {{OUTPUT_FILE}}")
    else: print("\\nNo leads found.")
if __name__=="__main__": asyncio.run(run_scraper())
'''

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
DAILY_LIMIT=50
DELAY=60
def build_email(name):
    subject=f"Quick question for {{name}}"
    body=f"""Hey {{name}},

Was checking out your website and noticed you still had some unbooked appointments. Quick question, are you getting consistent leads online or mostly word of mouth?

I help local service businesses get 20-30 qualified leads every month using paid ads.

Worth a quick 10 min call? Book a time here: https://lustrous-lollipop-5cd993.netlify.app/

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

FOLLOWUP_TEMPLATE = '''import base64,csv,os,time,pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
LEADS_FILE=r"C:\\peakline\\leads_{niche}.csv"
CREDENTIALS_FILE=r"C:\\peakline\\credentials.json"
TOKEN_FILE=r"C:\\peakline\\token.pickle"
SCOPES=["https://www.googleapis.com/auth/gmail.send","https://www.googleapis.com/auth/gmail.readonly"]
SENDER_NAME="Peakline Marketing"
SENDER_EMAIL="peakline.org@gmail.com"
DAILY_LIMIT=50
DELAY=60
def build_email(name):
    subject=f"Re: Quick question for {{name}}"
    body=f"""Hey {{name}},

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
def has_replied(service,email):
    try:
        results=service.users().messages().list(userId="me",q=f"from:{{email}}",maxResults=1).execute()
        return len(results.get("messages",[]))>0
    except: return False
def send_email(service,to,name):
    subject,body=build_email(name)
    msg=MIMEMultipart("alternative")
    msg["to"]=to; msg["subject"]=subject; msg["from"]=f"{{SENDER_NAME}} <{{SENDER_EMAIL}}>"
    msg.attach(MIMEText(body,"plain"))
    raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
    try: service.users().messages().send(userId="me",body={{"raw":raw}}).execute(); return True
    except HttpError as e: print(f"    [!] {{e}}"); return False
def run_followup(limit=DAILY_LIMIT):
    service=get_service()
    with open(LEADS_FILE,"r",encoding="utf-8") as f: leads=list(csv.DictReader(f))
    pending=[l for l in leads if l.get("email") and l.get("status")=="sent"][:limit]
    if not pending: print("No leads to follow up with."); return
    print(f"Checking {{len(pending)}} leads for replies...\\n")
    sent=0
    for i,lead in enumerate(pending):
        email=lead["email"]; name=lead["business_name"]
        print(f"[{{i+1}}/{{len(pending)}}] {{name}} <{{email}}>")
        if has_replied(service,email):
            lead["status"]="replied"; print("    Already replied - skipping.")
        else:
            if send_email(service,email,name):
                lead["status"]="followup_sent"; sent+=1; print("    Follow-up sent!")
            else: lead["status"]="followup_failed"; print("    Failed.")
            if i<len(pending)-1: print(f"    Waiting {{DELAY}}s..."); time.sleep(DELAY)
        with open(LEADS_FILE,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=leads[0].keys()); w.writeheader(); w.writerows(leads)
    print(f"\\nDone. Sent {{sent}} follow-ups.")
if __name__=="__main__": run_followup()
'''

EMAIL_FINDER = '''import csv,re,time,requests,sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse
EMAIL_REGEX=re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+")
HEADERS={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
SKIP_DOMAINS={"gmail.com","yahoo.com","hotmail.com","outlook.com","example.com"}
SKIP_PREFIXES=("noreply","no-reply","donotreply","support@","info@wix","info@squarespace")
def is_valid_email(e):
    d=e.split("@")[-1].lower()
    return d not in SKIP_DOMAINS and not any(e.lower().startswith(p) for p in SKIP_PREFIXES)
def find_email(website):
    if not website: return ""
    if not website.startswith("http"): website="https://"+website
    try:
        resp=requests.get(website,headers=HEADERS,timeout=10)
        emails=[e for e in EMAIL_REGEX.findall(resp.text) if is_valid_email(e)]
        if emails: return emails[0]
        base=f"{urlparse(website).scheme}://{urlparse(website).netloc}"
        for path in ["/contact","/contact-us","/about","/about-us"]:
            try:
                r=requests.get(base+path,headers=HEADERS,timeout=8)
                emails=[e for e in EMAIL_REGEX.findall(r.text) if is_valid_email(e)]
                if emails: return emails[0]
            except: pass
    except Exception as e: print(f"    [!] {e}")
    return ""
def run_email_finder(leads_file):
    with open(leads_file,"r",encoding="utf-8") as f: leads=list(csv.DictReader(f))
    updated=0
    for i,lead in enumerate(leads):
        if lead.get("email") or not lead.get("website"):
            print(f"[{i+1}/{len(leads)}] {lead[\'business_name\']} - skipping"); continue
        print(f"[{i+1}/{len(leads)}] {lead[\'business_name\']} - {lead[\'website\']}")
        email=find_email(lead["website"])
        if email: lead["email"]=email; updated+=1; print(f"    Found: {email}")
        else: print("    No email found")
        time.sleep(1)
    with open(leads_file,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=leads[0].keys()); w.writeheader(); w.writerows(leads)
    print(f"\\nDone. Found emails for {updated} leads.")
if __name__=="__main__":
    niche=sys.argv[1] if len(sys.argv)>1 else input("Which niche? (detailing/landscaping): ")
    run_email_finder(rf"C:\\peakline\\leads_{niche}.csv")
'''

CLEAN = '''import csv,re,sys
pattern=re.compile(r\'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z]{2,}$\')
def run_clean(leads_file):
    with open(leads_file,"r",encoding="utf-8") as f: leads=list(csv.DictReader(f))
    cleaned=0
    for lead in leads:
        email=lead.get("email","").strip().rstrip(".")
        if email and not pattern.match(email):
            print(f"Removing bad email: {email}")
            lead["email"]=""; lead["status"]="new"; cleaned+=1
        elif email: lead["email"]=email
    with open(leads_file,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=leads[0].keys()); w.writeheader(); w.writerows(leads)
    print(f"Cleaned {cleaned} bad emails.")
if __name__=="__main__":
    niche=sys.argv[1] if len(sys.argv)>1 else input("Which niche? (detailing/landscaping): ")
    run_clean(rf"C:\\peakline\\leads_{niche}.csv")
'''

files = {
    "scraper_detailing.py": SCRAPER_TEMPLATE.format(cities=CITIES, niche="detailing", search="auto detailing"),
    "scraper_landscaping.py": SCRAPER_TEMPLATE.format(cities=CITIES, niche="landscaping", search="landscaping"),
    "sender_detailing.py": SENDER_TEMPLATE.format(niche="detailing"),
    "sender_landscaping.py": SENDER_TEMPLATE.format(niche="landscaping"),
    "followup_detailing.py": FOLLOWUP_TEMPLATE.format(niche="detailing"),
    "followup_landscaping.py": FOLLOWUP_TEMPLATE.format(niche="landscaping"),
    "email_finder.py": EMAIL_FINDER,
    "clean.py": CLEAN,
}

for filename, content in files.items():
    with open(rf"C:\peakline\{filename}", "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {filename}")

# Rename leads.csv to leads_detailing.csv if it exists
import os
if os.path.exists(r"C:\peakline\leads.csv") and not os.path.exists(r"C:\peakline\leads_detailing.csv"):
    os.rename(r"C:\peakline\leads.csv", r"C:\peakline\leads_detailing.csv")
    print("Renamed leads.csv to leads_detailing.csv")

print("\nAll done! Your command board:")
print("--- DETAILING ---")
print("python C:\\peakline\\scraper_detailing.py")
print("python C:\\peakline\\email_finder.py detailing")
print("python C:\\peakline\\clean.py detailing")
print("python C:\\peakline\\sender_detailing.py")
print("python C:\\peakline\\followup_detailing.py")
print("--- LANDSCAPING ---")
print("python C:\\peakline\\scraper_landscaping.py")
print("python C:\\peakline\\email_finder.py landscaping")
print("python C:\\peakline\\clean.py landscaping")
print("python C:\\peakline\\sender_landscaping.py")
print("python C:\\peakline\\followup_landscaping.py")
