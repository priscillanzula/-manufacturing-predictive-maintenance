
# send_alerts.py
# Checks Supabase for engines in danger zone and sends an email alert to danielpriscilla61@gmail.com

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
from datetime import datetime


# SECURE CONFIGURATION (NO FALLBACK SECRETS)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")


# FAIL FAST IF MISSING

required_vars = {
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_KEY": SUPABASE_KEY,
    "GMAIL_ADDRESS": GMAIL_ADDRESS,
    "GMAIL_APP_PASSWORD": GMAIL_APP_PASSWORD,
    "ALERT_EMAIL_TO": ALERT_EMAIL_TO
}

missing = [key for key, value in required_vars.items() if not value]

if missing:
    raise ValueError(f"Missing environment variables: {', '.join(missing)}")

# CONNECT TO SUPABASE
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# GET LATEST READING PER ENGINE
print("Fetching latest engine readings from Supabase...")

response = supabase.table("engine_readings") \
    .select("engine_id, cycle, rul_capped, is_anomaly") \
    .order("cycle", desc=True) \
    .execute()

data = response.data

# Get the latest reading per engine
latest = {}
for row in data:
    eng_id = row["engine_id"]
    if eng_id not in latest:
        latest[eng_id] = row

latest_readings = list(latest.values())

# IDENTIFY DANGER AND WARNING ENGINES
danger_engines = [r for r in latest_readings if r["rul_capped"]
                  is not None and r["rul_capped"] < 30]
warning_engines = [r for r in latest_readings if r["rul_capped"]
                   is not None and 30 <= r["rul_capped"] < 80]
anomaly_engines = [r for r in latest_readings if r.get("is_anomaly") == True]

print(f"Danger engines: {len(danger_engines)}")
print(f"Warning engines: {len(warning_engines)}")
print(f"Anomaly detections: {len(anomaly_engines)}")

# Only send email if there is something to alert about
if not danger_engines and not anomaly_engines:
    print("No critical alerts. No email sent.")
    exit(0)

# BUILD EMAIL
now = datetime.now().strftime("%Y-%m-%d %H:%M")

danger_rows = ""
for r in sorted(danger_engines, key=lambda x: x["rul_capped"]):
    danger_rows += f"""
    <tr style="background-color:#fadbd8;">
        <td style="padding:8px;">Engine {r['engine_id']}</td>
        <td style="padding:8px;">{int(r['rul_capped'])} cycles</td>
        <td style="padding:8px;">🔴 DANGER</td>
    </tr>"""

warning_rows = ""
for r in sorted(warning_engines, key=lambda x: x["rul_capped"])[:5]:
    warning_rows += f"""
    <tr style="background-color:#fef9e7;">
        <td style="padding:8px;">Engine {r['engine_id']}</td>
        <td style="padding:8px;">{int(r['rul_capped'])} cycles</td>
        <td style="padding:8px;">🟡 WARNING</td>
    </tr>"""

html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color:#e74c3c;">✈️ Engine Health Alert — {now}</h2>
    <p>This is your automated engine health monitoring report.</p>

    <h3 style="color:#e74c3c;">🔴 DANGER — Immediate Maintenance Required ({len(danger_engines)} engines)</h3>
    <table border="1" cellspacing="0" cellpadding="0" style="border-collapse:collapse; width:100%;">
        <tr style="background-color:#2c3e50; color:white;">
            <th style="padding:8px;">Engine</th>
            <th style="padding:8px;">Cycles Remaining</th>
            <th style="padding:8px;">Status</th>
        </tr>
        {danger_rows if danger_rows else '<tr><td colspan="3" style="padding:8px;">None</td></tr>'}
    </table>

    <br>

    <h3 style="color:#f39c12;">🟡 WARNING — Schedule Maintenance Soon (top 5 of {len(warning_engines)})</h3>
    <table border="1" cellspacing="0" cellpadding="0" style="border-collapse:collapse; width:100%;">
        <tr style="background-color:#2c3e50; color:white;">
            <th style="padding:8px;">Engine</th>
            <th style="padding:8px;">Cycles Remaining</th>
            <th style="padding:8px;">Status</th>
        </tr>
        {warning_rows if warning_rows else '<tr><td colspan="3" style="padding:8px;">None</td></tr>'}
    </table>

    <br>
    <p style="color:#7f8c8d; font-size:12px;">
        This alert was sent automatically by your Engine Health Monitoring system.<br>
        View the full dashboard for more details.
    </p>
</body>
</html>
"""


# SEND EMAIL VIA GMAIL
msg = MIMEMultipart("alternative")
msg["Subject"] = f"🔴 Engine Alert: {len(danger_engines)} engines need immediate attention — {now}"
msg["From"] = GMAIL_ADDRESS
msg["To"] = ALERT_EMAIL_TO

msg.attach(MIMEText(html_body, "html"))

try:
    print("Sending alert email...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, ALERT_EMAIL_TO, msg.as_string())
    print(f"Alert email sent to {ALERT_EMAIL_TO}")
except Exception as e:
    print(f"Failed to send email: {e}")
    raise
