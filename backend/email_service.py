import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@imogenrfp.local")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    def send_invitation_email(self, to_email: str, invitation_token: str, tenant_name: str, invited_by_name: str) -> bool:
        """Send tenant invitation email"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Invitation to join {tenant_name} on ImogenRFP"
            msg['From'] = self.from_email
            msg['To'] = to_email

            # Create invitation URL
            invitation_url = f"{self.frontend_url}/invitation/accept?token={invitation_token}"

            # HTML email content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>You're invited to join {tenant_name}</title>
            </head>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #333; margin-bottom: 20px;">You're invited to join {tenant_name}</h2>
                    <p style="color: #666; line-height: 1.6;">
                        {invited_by_name} has invited you to join their organization "{tenant_name}" on ImogenRFP, 
                        an AI-powered RFP processing and response platform.
                    </p>
                    <p style="color: #666; line-height: 1.6;">
                        Click the button below to accept the invitation and create your account:
                    </p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{invitation_url}" 
                           style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: 600;">
                            Accept Invitation
                        </a>
                    </div>
                    <p style="color: #999; font-size: 14px; margin-top: 30px;">
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="{invitation_url}" style="color: #3b82f6; word-break: break-all;">{invitation_url}</a>
                    </p>
                    <p style="color: #999; font-size: 12px; margin-top: 20px;">
                        This invitation will expire in 7 days. If you don't want to join this organization, you can safely ignore this email.
                    </p>
                </div>
            </body>
            </html>
            """

            # Plain text fallback
            text_content = f"""
            You're invited to join {tenant_name}

            {invited_by_name} has invited you to join their organization "{tenant_name}" on ImogenRFP.

            Accept the invitation by visiting this link:
            {invitation_url}

            This invitation will expire in 7 days.
            """

            # Attach parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                
                server.send_message(msg)
                logger.info(f"Invitation email sent to {to_email} for tenant {tenant_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to send invitation email to {to_email}: {e}")
            return False

    def send_test_email(self, to_email: str) -> bool:
        """Send test email to verify email service is working"""
        try:
            msg = MIMEText("This is a test email from ImogenRFP email service.")
            msg['Subject'] = "ImogenRFP Email Service Test"
            msg['From'] = self.from_email
            msg['To'] = to_email

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                
                server.send_message(msg)
                logger.info(f"Test email sent to {to_email}")
                return True

        except Exception as e:
            logger.error(f"Failed to send test email to {to_email}: {e}")
            return False

email_service = EmailService()