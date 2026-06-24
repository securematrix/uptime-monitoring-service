import smtplib
from email.mime.text import MIMEText
import requests
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Simple in-memory struct to track alert cooldowns to avoid spam
ALERT_COOLDOWNS = {}
COOLDOWN_PERIOD = 300  # 5 minutes

def should_send_alert(monitor_id):
    last_sent = ALERT_COOLDOWNS.get(monitor_id)
    if last_sent is None:
        return True
    
    time_since = (datetime.now() - last_sent).total_seconds()
    return time_since >= COOLDOWN_PERIOD

def send_alert(monitor, message):
    if not should_send_alert(monitor.id):
        logger.info(f"Alert for monitor {monitor.id} suppressed due to cooldown.")
        return

    logger.warning(f"ALERT for {monitor.name}: {message}")
    
    subject = f"Uptime Alert: {monitor.name} is DOWN"
    
    if monitor.alert_email:
        send_email_alert(monitor.alert_email, subject, message)
        
    if monitor.alert_webhook:
        send_webhook_alert(monitor.alert_webhook, subject, message)
        
    ALERT_COOLDOWNS[monitor.id] = datetime.now()

def send_email_alert(to_email, subject, body):
    # Dummy implementation for SMTP - in production use real credentials
    smtp_server = os.getenv("SMTP_SERVER", "localhost")
    smtp_port = int(os.getenv("SMTP_PORT", 1025)) # Default to mailhog or similar
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    from_email = os.getenv("SMTP_FROM", "alerts@uptimeservice.local")
    
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info(f"Email alert sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")

def send_webhook_alert(webhook_url, subject, body):
    try:
        payload = {
            "text": f"**{subject}**\n{body}"
        }
        res = requests.post(webhook_url, json=payload, timeout=5.0)
        res.raise_for_status()
        logger.info(f"Webhook alert sent to {webhook_url}")
    except Exception as e:
        logger.error(f"Failed to send webhook alert: {e}")
