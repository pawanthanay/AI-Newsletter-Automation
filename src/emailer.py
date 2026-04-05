"""
Email sender — sends the HTML newsletter via Gmail SMTP.
Supports Gmail App Passwords for secure authentication.
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

logger = logging.getLogger(__name__)

# Gmail SMTP settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


class EmailSender:
    """Sends HTML emails via Gmail SMTP."""

    def __init__(self, config: dict):
        self.config = config
        email_config = config.get("email", {})
        self.sender = email_config.get("sender", "")
        self.receiver = email_config.get("receiver", "")
        self.app_password = email_config.get("app_password", "")
        self.subject_template = email_config.get("subject", "☀️ Your Daily AI Updates — {date}")

    def send(self, html_content: str) -> bool:
        """Send the newsletter email."""
        if not self._validate():
            return False

        today = datetime.now().strftime("%B %d, %Y")
        subject = self.subject_template.replace("{date}", today)

        msg = MIMEMultipart("alternative")
        msg["From"] = f"AI Newsletter Bot <{self.sender}>"
        msg["To"] = self.receiver
        msg["Subject"] = subject
        msg["X-Priority"] = "3"  # Normal priority

        # Plain text fallback
        plain_text = (
            f"Daily AI Brief — {today}\n\n"
            "Your daily AI newsletter is ready. "
            "Please view this email in an HTML-capable client for the best experience.\n\n"
            "— AI Newsletter Bot"
        )

        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        # Auto-detect SMTP server based on email domain
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        domain = self.sender.split('@')[-1].lower() if '@' in self.sender else ''
        if 'yahoo.com' in domain or 'ymail.com' in domain:
            smtp_server = "smtp.mail.yahoo.com"
            smtp_port = 465  # Force SSL for Yahoo
        elif 'outlook.com' in domain or 'hotmail.com' in domain:
            smtp_server = "smtp-mail.outlook.com"
        elif 'office365.com' in domain:
            smtp_server = "smtp.office365.com"

        try:
            logger.info(f"📧 Connecting to SMTP server ({smtp_server}:{smtp_port})...")
            if smtp_port == 465:
                # Use implicit SSL
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(self.sender, self.app_password)
                    server.sendmail(self.sender, self.receiver, msg.as_string())
            else:
                # Use explicit TLS
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.sender, self.app_password)
                    server.sendmail(self.sender, self.receiver, msg.as_string())

            logger.info(f"✅ Newsletter sent successfully to {self.receiver}")
            return True

        except smtplib.SMTPAuthenticationError:
            provider = "Gmail" if "gmail" in smtp_server else "Yahoo/Outlook" 
            logger.error(
                f"❌ {provider} authentication failed! "
                "Make sure you're using an App Password, not your regular password.\n"
                "  → For Gmail: Google Account → Security → 2-Step Verification → App Passwords\n"
                "  → For Yahoo: Account Security → Generate and manage app passwords\n"
                "  → Update config.yaml with the generated app password"
            )
            return False

        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            return False

        except Exception as e:
            logger.error(f"❌ Unexpected email error: {e}")
            return False

    def _validate(self) -> bool:
        """Validate email configuration."""
        if not self.sender or self.sender == "your_email@gmail.com":
            logger.error("❌ Email sender not configured. Update config.yaml")
            return False

        if not self.receiver or self.receiver == "your_email@gmail.com":
            logger.error("❌ Email receiver not configured. Update config.yaml")
            return False

        if not self.app_password or self.app_password == "your_gmail_app_password":
            logger.error(
                "❌ Gmail App Password not configured. Update config.yaml\n"
                "  → Go to: Google Account → Security → 2-Step Verification → App Passwords"
            )
            return False

        return True

    def send_test(self) -> bool:
        """Send a test email to verify configuration."""
        test_html = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 40px; text-align: center;
                     background: #0f0f13; color: #e8e8ed;">
            <h1 style="color: #6c5ce7;">✅ AI Newsletter Setup Complete!</h1>
            <p style="font-size: 16px; color: #9898a8;">
                Your email configuration is working correctly.<br>
                You'll receive your daily AI updates at the scheduled time.
            </p>
            <p style="margin-top: 30px; font-size: 13px; color: #666;">
                — AI Newsletter Bot
            </p>
        </body>
        </html>
        """
        logger.info("📧 Sending test email...")
        return self.send(test_html)
