"""Email service — sends transactional emails via SMTP."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class EmailService:
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.sender = settings.SMTP_FROM

    async def send(self, to: str, subject: str, html: str, text: Optional[str] = None):
        if not self.user or not self.password:
            logger.warning("email_not_configured", to=to, subject=subject)
            return  # Silently skip in dev when SMTP not configured

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = to

        if text:
            msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.sender, [to], msg.as_string())
            logger.info("email_sent", to=to, subject=subject)
        except Exception as e:
            logger.error("email_send_failed", to=to, error=str(e))

    async def send_verification_email(self, to: str, name: str, token: str):
        url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        html = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
          <h2 style="color:#6366f1">Verify your Atlas AI account</h2>
          <p>Hi {name},</p>
          <p>Click the button below to verify your email address.</p>
          <a href="{url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600">
            Verify Email
          </a>
          <p style="color:#666;font-size:12px;margin-top:24px">Link expires in 7 days. If you didn't create an account, ignore this email.</p>
        </div>
        """
        await self.send(to, "Verify your Atlas AI account", html)

    async def send_password_reset_email(self, to: str, name: str, token: str):
        url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        html = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
          <h2 style="color:#6366f1">Reset your password</h2>
          <p>Hi {name},</p>
          <p>Click the button below to reset your Atlas AI password. This link expires in 1 hour.</p>
          <a href="{url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600">
            Reset Password
          </a>
          <p style="color:#666;font-size:12px;margin-top:24px">If you didn't request this, ignore this email.</p>
        </div>
        """
        await self.send(to, "Reset your Atlas AI password", html)

    async def send_workspace_invitation(self, to: str, inviter_name: str, workspace_name: str, role: str):
        url = f"{settings.FRONTEND_URL}/workspaces"
        html = f"""
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
          <h2 style="color:#6366f1">You've been invited to Atlas AI</h2>
          <p><strong>{inviter_name}</strong> has invited you to join <strong>{workspace_name}</strong> as {role}.</p>
          <a href="{url}" style="display:inline-block;background:#6366f1;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600">
            Accept Invitation
          </a>
        </div>
        """
        await self.send(to, f"Invitation to {workspace_name} on Atlas AI", html)
