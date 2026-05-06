from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.model.user import User, Role, UserProfile
from app.model.log import OperationLog
from app.service.auth_service import AuthService


class UserService:
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_users(
        db: Session,
        role: str = None,
        is_active: bool = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[User]:
        query = db.query(User)
        if role:
            query = query.join(Role).filter(Role.name == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        return query.offset((page - 1) * page_size).limit(page_size).all()
    
    @staticmethod
    def update_user(
        db: Session,
        user: User,
        email: str = None,
        current_user_id: int = None
    ) -> User:
        if email:
            existing = UserService.get_user_by_email(db, email)
            if existing and existing.id != user.id:
                raise ValueError("Email already in use")
            user.email = email
        db.commit()
        db.refresh(user)
        
        if current_user_id:
            log = OperationLog(
                user_id=current_user_id,
                action="UPDATE_USER",
                target_type="user",
                target_id=user.id,
                details=f'{{"email": "{email}"}}'
            )
            db.add(log)
            db.commit()
        
        return user
    
    @staticmethod
    def change_password(
        db: Session,
        user: User,
        old_password: str,
        new_password: str
    ) -> bool:
        if not AuthService.verify_password(old_password, user.password_hash):
            return False
        user.password_hash = AuthService.hash_password(new_password)
        db.commit()
        return True
    
    @staticmethod
    def create_user(
        db: Session,
        username: str,
        email: str,
        password: str,
        role_name: str = "customer",
        created_by: int = None
    ) -> User:
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise ValueError(f"Role '{role_name}' not found")
        
        password_hash = AuthService.hash_password(password)
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role_id=role.id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        if created_by:
            log = OperationLog(
                user_id=created_by,
                action="CREATE_USER",
                target_type="user",
                target_id=user.id,
                details=f'{{"username": "{username}", "role": "{role_name}"}}'
            )
            db.add(log)
            db.commit()
        
        return user
    
    @staticmethod
    def deactivate_user(db: Session, user_id: int, by_user_id: int) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        user.is_active = False
        db.commit()
        
        log = OperationLog(
            user_id=by_user_id,
            action="DEACTIVATE_USER",
            target_type="user",
            target_id=user_id
        )
        db.add(log)
        db.commit()
        return True
    
    @staticmethod
    def get_user_profile(db: Session, user_id: int) -> Optional[UserProfile]:
        return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    @staticmethod
    def create_or_update_profile(
        db: Session,
        user_id: int,
        preference: str = None,
        activity_score: int = 0
    ) -> UserProfile:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            if preference:
                profile.preference = preference
            if activity_score is not None:
                profile.activity_score = activity_score
            profile.last_analysis_at = datetime.utcnow()
        else:
            profile = UserProfile(
                user_id=user_id,
                preference=preference,
                activity_score=activity_score
            )
            db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile