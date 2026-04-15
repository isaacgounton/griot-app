"""
Email service for sending verification and notification emails via Resend.
"""
import os
from typing import Optional
from loguru import logger

# Try to import resend, but don't fail if not installed
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("resend package not installed. Email functionality will be disabled.")

# Get email configuration from environment
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "noreply@example.com")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Griot")

def initialize_resend():
    """Initialize the Resend email client."""
    if RESEND_AVAILABLE and RESEND_API_KEY:
        resend.api_key = RESEND_API_KEY
        logger.info("✅ Resend email service initialized")
    else:
        logger.warning("⚠️  Resend not configured. Email functionality disabled.")

async def send_verification_email(
    email: str,
    full_name: str,
    verification_token: str,
    verification_url: Optional[str] = None
) -> bool:
    """
    Send an email verification link to a user.
    
    Args:
        email: Recipient email address
        full_name: Recipient's full name
        verification_token: Token for email verification
        verification_url: Optional custom verification URL (defaults to frontend URL)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    if not RESEND_AVAILABLE:
        logger.error("❌ Resend package not available")
        return False
    
    if not RESEND_API_KEY:
        logger.error("❌ RESEND_API_KEY not configured")
        return False
    
    if not verification_url:
        # Build the verification URL from environment or use localhost default
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        verification_url = f"{frontend_url}/verify-email?token={verification_token}"
    
    try:
        # Extract first name for personalization
        first_name = full_name.split()[0] if full_name else "User"
        
        # Create email body with HTML formatting
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        color: #333;
                        line-height: 1.6;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .header h1 {{
                        color: #2563eb;
                        margin: 0;
                    }}
                    .content {{
                        background: #f9fafb;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                    .button {{
                        display: inline-block;
                        background: #2563eb;
                        color: white;
                        padding: 12px 30px;
                        text-decoration: none;
                        border-radius: 6px;
                        margin: 20px 0;
                        font-weight: 600;
                    }}
                    .button:hover {{
                        background: #1d4ed8;
                    }}
                    .footer {{
                        font-size: 12px;
                        color: #6b7280;
                        text-align: center;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #e5e7eb;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to {EMAIL_FROM_NAME}!</h1>
                    </div>
                    
                    <div class="content">
                        <p>Hi {first_name},</p>
                        <p>Thank you for registering! To complete your registration and verify your email address, please click the button below:</p>
                        
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Email Address</a>
                        </div>
                        
                        <p>Or copy and paste this link in your browser:</p>
                        <p style="word-break: break-all; font-size: 12px; color: #666;">
                            {verification_url}
                        </p>
                        
                        <p style="margin-top: 30px; font-size: 14px;">
                            This link will expire in 24 hours for security reasons.
                        </p>
                        
                        <p style="margin-top: 20px;">
                            If you didn't create this account, you can safely ignore this email.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2024 {EMAIL_FROM_NAME}. All rights reserved.</p>
                        <p>This is an automated message, please do not reply to this email.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Initialize Resend client
        initialize_resend()
        
        # Send email using Resend
        email_response = resend.Emails.send({
            "from": f"{EMAIL_FROM_NAME} <{EMAIL_FROM_ADDRESS}>",
            "to": email,
            "subject": f"Verify your {EMAIL_FROM_NAME} email address",
            "html": html_content,
        })
        
        if email_response.get("id"):
            logger.info(f"✅ Verification email sent to {email} (ID: {email_response.get('id')})")
            return True
        else:
            logger.error(f"❌ Failed to send verification email: {email_response}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending verification email to {email}: {str(e)}")
        return False

async def send_welcome_email(
    email: str,
    full_name: str
) -> bool:
    """
    Send a welcome email to a verified user.
    
    Args:
        email: Recipient email address
        full_name: Recipient's full name
        
    Returns:
        True if email sent successfully, False otherwise
    """
    if not RESEND_AVAILABLE:
        logger.error("❌ Resend package not available")
        return False
    
    if not RESEND_API_KEY:
        logger.error("❌ RESEND_API_KEY not configured")
        return False
    
    try:
        first_name = full_name.split()[0] if full_name else "User"
        dashboard_url = os.getenv("FRONTEND_URL", "http://localhost:5173") + "/dashboard"
        
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        color: #333;
                        line-height: 1.6;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .header h1 {{
                        color: #2563eb;
                        margin: 0;
                    }}
                    .content {{
                        background: #f9fafb;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                    .button {{
                        display: inline-block;
                        background: #2563eb;
                        color: white;
                        padding: 12px 30px;
                        text-decoration: none;
                        border-radius: 6px;
                        margin: 20px 0;
                        font-weight: 600;
                    }}
                    .button:hover {{
                        background: #1d4ed8;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to {EMAIL_FROM_NAME}, {first_name}!</h1>
                    </div>
                    
                    <div class="content">
                        <p>Your email has been verified successfully. You're all set!</p>
                        
                        <p>Start exploring your dashboard:</p>
                        
                        <div style="text-align: center;">
                            <a href="{dashboard_url}" class="button">Go to Dashboard</a>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Initialize Resend client
        initialize_resend()
        
        # Send email
        email_response = resend.Emails.send({
            "from": f"{EMAIL_FROM_NAME} <{EMAIL_FROM_ADDRESS}>",
            "to": email,
            "subject": f"Welcome to {EMAIL_FROM_NAME}!",
            "html": html_content,
        })
        
        if email_response.get("id"):
            logger.info(f"✅ Welcome email sent to {email} (ID: {email_response.get('id')})")
            return True
        else:
            logger.error(f"❌ Failed to send welcome email: {email_response}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending welcome email to {email}: {str(e)}")
        return False
