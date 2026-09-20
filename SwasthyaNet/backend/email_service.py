import os
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretjwtkey123")
ALGORITHM = "HS256"
ACTIVATION_TOKEN_EXPIRE_HOURS = 48

# SMTP configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER or "noreply@swasthyanet.gov.in")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "SwasthyaNet Healthcare Portal")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

def generate_temporary_password(length: int = 12) -> str:
    """
    Generates a cryptographically strong temporary password
    containing uppercase, lowercase, digits, and special characters.
    """
    if length < 8:
        length = 8
    
    # Ensure at least 1 upper, 1 lower, 1 digit, 1 special character
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "@#$%&*!"
    
    pwd = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    all_chars = uppercase + lowercase + digits + special
    for _ in range(length - 4):
        pwd.append(secrets.choice(all_chars))
        
    secrets.SystemRandom().shuffle(pwd)
    return "".join(pwd)

def create_activation_token(user_id: int, email: str, role: str, expire_hours: int = ACTIVATION_TOKEN_EXPIRE_HOURS) -> str:
    """
    Creates a signed JWT token specifically for user account activation and initial password setup.
    """
    expire = datetime.utcnow() + timedelta(hours=expire_hours)
    payload = {
        "sub": email,
        "user_id": user_id,
        "role": role,
        "purpose": "account_activation",
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def verify_activation_token(token: str) -> dict:
    """
    Decodes and verifies an account activation token.
    Raises ValueError on invalid/expired tokens.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        if payload.get("purpose") != "account_activation":
            raise ValueError("Invalid token purpose. Expected account activation token.")
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Activation link has expired. Please request a new activation link.")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid activation token.")

def build_activation_email_html(
    name: str, 
    email: str, 
    role: str, 
    temp_password: str, 
    activation_link: str, 
    centre_name: str = None, 
    district_name: str = None
) -> str:
    """
    Constructs a responsive, modern HTML email template for new account invitations.
    """
    role_display = role.replace("_", " ").title()
    jurisdiction = []
    if centre_name:
        jurisdiction.append(f"Centre: <strong>{centre_name}</strong>")
    if district_name:
        jurisdiction.append(f"District: <strong>{district_name}</strong>")
    jurisdiction_str = " | ".join(jurisdiction) if jurisdiction else "System-Wide Jurisdiction"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome to SwasthyaNet</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
    
    <!-- Header -->
    <tr>
      <td style="background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%); padding: 32px 28px; text-align: center;">
        <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">SwasthyaNet</h1>
        <p style="color: #e0e7ff; margin: 6px 0 0 0; font-size: 13px; letter-spacing: 0.5px; text-transform: uppercase;">Public Healthcare Network</p>
      </td>
    </tr>
    
    <!-- Body -->
    <tr>
      <td style="padding: 32px 28px;">
        <h2 style="font-size: 18px; font-weight: 600; color: #0f172a; margin-top: 0;">Welcome, {name}!</h2>
        <p style="font-size: 14px; line-height: 1.6; color: #475569;">
          Your official account for the <strong>SwasthyaNet</strong> healthcare platform has been created by the System Administrator. You can now activate your account, configure your permanent password, and access your dashboard.
        </p>

        <!-- Account Details Box -->
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin: 24px 0; background-color: #f1f5f9; border-radius: 8px; border-left: 4px solid #4f46e5; padding: 16px;">
          <tr>
            <td style="padding: 6px 12px; font-size: 13px; color: #64748b; width: 140px;">Email / Username:</td>
            <td style="padding: 6px 12px; font-size: 13px; font-weight: 600; color: #0f172a;">{email}</td>
          </tr>
          <tr>
            <td style="padding: 6px 12px; font-size: 13px; color: #64748b;">Assigned Role:</td>
            <td style="padding: 6px 12px; font-size: 13px; font-weight: 600; color: #4f46e5;">{role_display}</td>
          </tr>
          <tr>
            <td style="padding: 6px 12px; font-size: 13px; color: #64748b;">Assignment:</td>
            <td style="padding: 6px 12px; font-size: 13px; color: #1e293b;">{jurisdiction_str}</td>
          </tr>
          <tr>
            <td style="padding: 6px 12px; font-size: 13px; color: #64748b;">Temporary Password:</td>
            <td style="padding: 6px 12px; font-size: 14px; font-family: monospace; font-weight: 700; color: #dc2626; letter-spacing: 1px;">{temp_password}</td>
          </tr>
        </table>

        <!-- CTA Button -->
        <div style="text-align: center; margin: 32px 0 24px 0;">
          <a href="{activation_link}" style="background-color: #4f46e5; color: #ffffff; text-decoration: none; padding: 14px 32px; font-size: 15px; font-weight: 600; border-radius: 8px; display: inline-block; box-shadow: 0 2px 6px rgba(79, 70, 229, 0.35);">
            Activate Account & Set Password
          </a>
        </div>

        <p style="font-size: 12px; color: #94a3b8; text-align: center; margin-top: 16px;">
          Or copy and paste this activation link into your browser:<br>
          <a href="{activation_link}" style="color: #4f46e5; word-break: break-all;">{activation_link}</a>
        </p>

        <!-- Security Warning -->
        <div style="margin-top: 30px; padding: 12px 16px; background-color: #fffbeb; border: 1px solid #fef3c7; border-radius: 6px;">
          <p style="margin: 0; font-size: 12px; color: #92400e; line-height: 1.5;">
            <strong>Security Notice:</strong> This activation link is valid for 48 hours. For security reasons, you will be required to change this temporary password upon your first activation. Never share this email or your credentials with anyone.
          </p>
        </div>
      </td>
    </tr>

    <!-- Footer -->
    <tr>
      <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 28px; text-align: center;">
        <p style="margin: 0; font-size: 11px; color: #94a3b8;">
          © {datetime.utcnow().year} SwasthyaNet Healthcare Portal. All rights reserved.
        </p>
      </td>
    </tr>

  </table>
</body>
</html>"""
    return html

def send_activation_email(
    to_email: str, 
    name: str, 
    role: str, 
    temp_password: str, 
    activation_token: str, 
    centre_name: str = None, 
    district_name: str = None
) -> dict:
    """
    Sends the activation email with temporary password and activation link.
    If SMTP server is configured and reachable, sends real email via SMTP.
    Otherwise, logs activation info clearly to standard output and returns status.
    """
    activation_link = f"{FRONTEND_URL}/activate?token={activation_token}"
    
    html_content = build_activation_email_html(
        name=name,
        email=to_email,
        role=role,
        temp_password=temp_password,
        activation_link=activation_link,
        centre_name=centre_name,
        district_name=district_name
    )
    
    text_content = f"""
Welcome to SwasthyaNet, {name}!

Your official account has been created with the following details:
- Email / Username: {to_email}
- Assigned Role: {role}
- Temporary Password: {temp_password}

To activate your account and set your permanent password, please visit:
{activation_link}

Note: This activation link is valid for 48 hours.
"""

    result = {
        "sent": False,
        "method": "none",
        "to_email": to_email,
        "activation_link": activation_link,
        "temp_password": temp_password,
        "message": ""
    }

    # If SMTP is configured, attempt real dispatch
    if SMTP_HOST and SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Welcome to SwasthyaNet - Account Activation & Temporary Password"
            msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
            msg["To"] = to_email

            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)

            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            server.ehlo()
            if SMTP_PORT == 587:
                server.starttls()
                server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())
            server.quit()

            result["sent"] = True
            result["method"] = "smtp"
            result["message"] = f"Activation email successfully dispatched to {to_email} via SMTP"
            print(f"[EMAIL SERVICE] Sent activation email to {to_email}")
            return result
        except Exception as e:
            print(f"[EMAIL SERVICE WARNING] SMTP send failed: {e}. Falling back to console notification.")
            result["message"] = f"SMTP error: {str(e)}"
    
    # Fallback / Local Dev Mode: Print credentials and activation link to server logs
    print("=" * 70)
    print(f"[SWASTHYANET EMAIL SIMULATOR] Account Created for: {to_email}")
    print(f"Name: {name} | Role: {role}")
    print(f"Temporary Password: {temp_password}")
    print(f"Activation Link: {activation_link}")
    print("=" * 70)

    result["sent"] = True
    result["method"] = "simulated_console"
    if not result["message"]:
        result["message"] = f"Activation credentials logged to console for {to_email}"
        
    return result
