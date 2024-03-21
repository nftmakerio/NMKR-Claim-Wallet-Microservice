from config import GMAIL_USER, GMAIL_PASSWORD, WALLET_PASSWORD
from email.message import EmailMessage
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(to_email, magic_link, template):
    msg = MIMEMultipart()
    msg['Subject'] = 'Confirm your email address'
    msg['From'] = 'noreply@nmkr.io'
    msg['To'] = to_email
    
    if template == "verify_mail":
        # Load HTML content from a file
        with open('verify_mail.html', 'r') as file:
            html_content = file.read().replace("{magic_link}", magic_link)
    elif template == 'existing_wallet':
        # Load HTML content from a file
        with open('verify_mail_existing_wallet.html', 'r') as file:
            html_content = file.read().replace("{magic_link}", magic_link)

    
    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_PASSWORD)
        smtp.send_message(msg)
