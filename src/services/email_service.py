import smtplib
from email.message import EmailMessage
import os
import mimetypes

def send_report_email(filepath: str, to_email: str):
    """
    Sends the generated Excel report via Gmail SMTP.
    Uses environment variables for credentials.
    """
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    
    if not smtp_user or not smtp_password:
        print("Warning: SMTP_USER or SMTP_PASSWORD not set. Skipping email delivery.")
        return False
        
    if not to_email:
        print("Warning: No destination email provided. Skipping email delivery.")
        return False

    msg = EmailMessage()
    msg['Subject'] = 'Automated Trading Report (Growth Invest Plan)'
    msg['From'] = smtp_user
    msg['To'] = to_email
    
    msg.set_content(
        "Hello,\n\n"
        "Attached is your latest automated trading report encompassing the 9-point checklist, "
        "3 trading style setups, news catalysts, and earnings data, organized by sector.\n\n"
        "Happy Trading,\n"
        "Growth Invest Plan Automated System"
    )

    if filepath and os.path.exists(filepath):
        ctype, encoding = mimetypes.guess_type(filepath)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        
        with open(filepath, 'rb') as f:
            msg.add_attachment(f.read(),
                               maintype=maintype,
                               subtype=subtype,
                               filename=os.path.basename(filepath))
                               
    try:
        # Use SMTP_SSL for port 465
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
                
        print(f"Successfully sent report email to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
