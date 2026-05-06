import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.model.log import VerificationCode
from app.config import get_config
import secrets


class EmailService:
    
    @staticmethod
    def send_verification_code(db: Session, email: str, purpose: str = "register") -> tuple[str, str]:
        """
        发送验证码到邮箱
        返回: (error, code)
        """
        config = get_config()
        
        # 生成6位验证码
        code = secrets.randbelow(1000000)
        code_str = f"{code:06d}"
        
        # 过期时间 5分钟
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        # 保存验证码到数据库
        existing = db.query(VerificationCode).filter(
            VerificationCode.email == email,
            VerificationCode.purpose == purpose,
            VerificationCode.is_used == False
        ).all()
        
        for e in existing:
            e.is_used = True
        
        verification = VerificationCode(
            email=email,
            code=code_str,
            purpose=purpose,
            expires_at=expires_at
        )
        db.add(verification)
        db.commit()
        
        # 发送邮件
        if not config.smtp.username or not config.smtp.password:
            print(f"[Email] Would send verification code {code_str} to {email}")
            return None, code_str
        
        try:
            subject = "Verification Code"
            body = f"""
            <html>
            <body>
                <h2>Your Verification Code</h2>
                <p>Your verification code is: <strong>{code_str}</strong></p>
                <p>This code will expire in 5 minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
            </html>
            """
            
            msg = MIMEText(body, "html", "utf-8")
            msg["Subject"] = subject
            msg["From"] = config.smtp.username
            msg["To"] = email
            
            with smtplib.SMTP(config.smtp.host, config.smtp.port) as server:
                if config.smtp.use_tls:
                    server.starttls()
                server.login(config.smtp.username, config.smtp.password)
                server.sendmail(config.smtp.username, [email], msg.as_string())
            
            print(f"[Email] Verification code sent to {email}")
            return None, code_str
            
        except Exception as e:
            print(f"[Email] Failed to send verification code: {e}")
            return f"Failed to send email: {str(e)}", None
    
    @staticmethod
    def verify_code(db: Session, email: str, code: str, purpose: str = "register") -> bool:
        """
        验证验证码
        返回: True if valid, False otherwise
        """
        verification = db.query(VerificationCode).filter(
            VerificationCode.email == email,
            VerificationCode.code == code,
            VerificationCode.purpose == purpose,
            VerificationCode.is_used == False,
            VerificationCode.expires_at > datetime.utcnow()
        ).first()
        
        if verification:
            verification.is_used = True
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def send_new_password(db: Session, email: str, new_password: str) -> tuple[str, None]:
        """
        发送新密码到邮箱
        返回: (error, None)
        """
        config = get_config()
        
        try:
            subject = "Password Reset - Your New Password"
            body = f"""
            <html>
            <body>
                <h2>Password Reset</h2>
                <p>Your password has been reset. Here is your new password:</p>
                <p><strong style="font-size: 18px;">{new_password}</strong></p>
                <p>Please login with this password and change it immediately.</p>
                <p>If you didn't request a password reset, please contact support immediately.</p>
            </body>
            </html>
            """
            
            msg = MIMEText(body, "html", "utf-8")
            msg["Subject"] = subject
            msg["From"] = config.smtp.username
            msg["To"] = email
            
            with smtplib.SMTP(config.smtp.host, config.smtp.port) as server:
                if config.smtp.use_tls:
                    server.starttls()
                server.login(config.smtp.username, config.smtp.password)
                server.sendmail(config.smtp.username, [email], msg.as_string())
            
            print(f"[Email] New password sent to {email}")
            return None, None
            
        except Exception as e:
            print(f"[Email] Failed to send new password: {e}")
            return f"Failed to send email: {str(e)}", None