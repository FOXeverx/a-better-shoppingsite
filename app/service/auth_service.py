from datetime import datetime, timedelta
from typing import Optional, Tuple
import secrets
import bcrypt
from jose import jwt
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.model.user import User, Role
from app.model.log import LoginLog
from app.model.database import Base, engine
from app.config import get_config

config = get_config()


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    
    @staticmethod
    def create_access_token(user_id: int, role: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=config.jwt.expire_minutes)
        payload = {
            "sub": str(user_id),
            "role": role,
            "exp": expire
        }
        return jwt.encode(payload, config.jwt.secret, algorithm=config.jwt.algorithm)
    
    @staticmethod
    def create_confirm_token() -> str:
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def init_db():
        Base.metadata.create_all(bind=engine)
    
    @staticmethod
    def register(
        db: Session,
        username: str,
        email: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = None
    ) -> Tuple[Optional[User], Optional[str]]:
        password_hash = AuthService.hash_password(password)
        
        try:
            role = db.query(Role).filter(Role.name == "customer").first()
            if not role:
                role = Role(name="customer")
                db.add(role)
                db.flush()
            
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role_id=role.id
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            login_log = LoginLog(
                user_id=user.id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            db.add(login_log)
            db.commit()
            
            return user, None
        except IntegrityError as e:
            db.rollback()
            error_msg = str(e.orig)
            if "username" in error_msg.lower():
                return None, "Username already exists"
            elif "email" in error_msg.lower():
                return None, "Email already exists"
            return None, "Registration failed"
    
    @staticmethod
    def login(
        db: Session,
        username: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = None
    ) -> Tuple[Optional[User], Optional[str]]:
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            login_log = LoginLog(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False
            )
            db.add(login_log)
            db.commit()
            return None, "Invalid username or password"
        
        if not user.is_active:
            if user.blocked_until and user.blocked_until > datetime.utcnow():
                login_log = LoginLog(
                    user_id=user.id,
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False
                )
                db.add(login_log)
                db.commit()
                return None, "Account is temporarily blocked"
        
        if not AuthService.verify_password(password, user.password_hash):
            user.login_attempts += 1
            
            if user.login_attempts >= config.security.max_login_attempts:
                user.blocked_until = datetime.utcnow() + timedelta(
                    minutes=config.security.block_duration_minutes
                )
                login_log = LoginLog(
                    user_id=user.id,
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False
                )
                db.add(login_log)
                db.commit()
                return None, "Too many failed attempts. Account blocked."
            
            user.last_login_at = datetime.utcnow()
            db.commit()
            
            login_log = LoginLog(
                user_id=user.id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False
            )
            db.add(login_log)
            db.commit()
            return None, "Invalid username or password"
        
        user.login_attempts = 0
        user.blocked_until = None
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        login_log = LoginLog(
            user_id=user.id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        db.add(login_log)
        db.commit()
        
        return user, None
    
    @staticmethod
    def logout(user: User, db: Session):
        pass