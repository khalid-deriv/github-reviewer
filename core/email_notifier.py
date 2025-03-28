import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.logger import setup_logger

# Initialize logger
logger = setup_logger()

def send_email_notification(recipient_email, subject, message, smtp_server="smtp.gmail.com", smtp_port=587, sender_email=None, sender_password=None):
    """
    Send an email notification for critical issues.

    Args:
        recipient_email (str): The recipient's email address.
        subject (str): The subject of the email.
        message (str): The body of the email.
        smtp_server (str): The SMTP server to use (default: smtp.gmail.com).
        smtp_port (int): The SMTP server port (default: 587).
        sender_email (str): The sender's email address.
        sender_password (str): The sender's email password.

    Raises:
        ValueError: If required arguments are missing.
        Exception: If the email fails to send.
    """
    if not all([recipient_email, subject, message, sender_email, sender_password]):
        raise ValueError("Recipient email, subject, message, sender email, and sender password are required.")

    try:
        # Create the email
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        # Connect to the SMTP server and send the email
        logger.info(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            logger.info(f"Email sent successfully to {recipient_email}")

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise
