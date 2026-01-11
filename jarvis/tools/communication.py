"""
BRO Communication Tools
Send emails, WhatsApp messages, and manage communications.
"""

import smtplib
import webbrowser
import urllib.parse
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os

from .registry import tool


@tool("send_email", "Sends an email to a recipient. Requires SMTP configuration.", requires_confirmation=True)
def send_email(to_email: str, subject: str, body: str) -> str:
    """
    Sends an email using SMTP.
    
    Args:
        to_email: usage 'user@example.com'
        subject: Email subject
        body: Email body content
    """
    # Fallback config if not in global config
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    sender_email = os.environ.get("SMTP_EMAIL", "")
    sender_password = os.environ.get("SMTP_PASSWORD", "")
    
    if not sender_email or not sender_password:
        return "❌ SMTP credentials not found. Please set SMTP_EMAIL and SMTP_PASSWORD environment variables."

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        
        return f"✓ Email sent to {to_email}"
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"


@tool("send_whatsapp", "Sends a WhatsApp message explicitly via Web or Desktop. Use 'open whatsapp' for just checking.")
def send_whatsapp(phone_number: str, message: str) -> str:
    """
    Opens WhatsApp web/desktop with a pre-filled message.
    User must still press send (security feature of WA).
    
    Args:
        phone_number: Phone number with country code (e.g. "+1234567890")
        message: The text to send
    """
    try:
        # urlencode the message
        encoded_msg = urllib.parse.quote(message)
        
        # WhatsApp URL scheme
        # https://wa.me/number?text=message
        # Remove + and spaces/dashes from number for basic cleanup
        clean_number = phone_number.replace("+", "").replace(" ", "").replace("-", "")
        
        url = f"https://wa.me/{clean_number}?text={encoded_msg}"
        
        webbrowser.open(url)
        return f"✓ Opened WhatsApp draft to {phone_number}. Please press send."
    except Exception as e:
        return f"❌ Error opening WhatsApp: {str(e)}"
