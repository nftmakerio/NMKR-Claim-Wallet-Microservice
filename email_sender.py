from config import GMAIL_USER, GMAIL_PASSWORD, WALLET_PASSWORD
from email.message import EmailMessage
import smtplib

def send_email(to_email, magic_link):
    msg = EmailMessage()
    msg['Subject'] = 'Your Magic Link'
    msg['From'] = 'info@nft-maker.io'
    msg['To'] = to_email
    msg.set_content(f'Here is your magic link: {magic_link}\nIt is valid for 30 minutes.')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_PASSWORD)
        smtp.send_message(msg)
