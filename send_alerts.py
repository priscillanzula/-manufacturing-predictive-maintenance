# ============================================================
# send_alerts.py
# Checks Supabase for engines in danger zone and sends
# an email alert to danielpriscilla61@gmail.com
#
# This script is run automatically by GitHub Actions every hour
# You can also run it manually: python send_alerts.py
# ============================================================

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
from datetime import datetime

# ============================================================
# CREDENTIALS — stored as GitHub Secrets, not hardcoded
# ============================================================
SUPABASE_URL = os.environ.get(
    "SUPABASE_URL", "https://tqspwjsofhkubzwddjqj.supabase.co")
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRxc3B3anNvZmhrdWJ6d2RkanFqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0MDM5ODAsImV4cCI6MjA4ODk3OTk4MH0.5KMH4wIT_gOGAWPjiKjRU206NkY2Vu_7ly8ZlkYbdYE")

# Gmail credentials — use an App Password, not your real password
# Go to: Google Account > Security > 2-Step Verification > App Passwords
GMAIL_ADDRESS = "danielpriscilla61@gmail.com"
GMAIL_PASSWORD = os.environ.get(
    "GMAIL_APP_PASSWORD", "your-gmail-app-password")

ALERT_EMAIL_TO = "danielpriscilla61@gmail.com"

# ============================================================
# CONNECT TO SUPABASE
# ============================================================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# GET LATEST READING PER ENGINE
# ============================================================
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

# ============================================================
# IDENTIFY DANGER AND WARNING ENGINES
# ============================================================
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

# ============================================================
# BUILD EMAIL
# ============================================================
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

# ============================================================
# SEND EMAIL VIA GMAIL
# ============================================================
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
