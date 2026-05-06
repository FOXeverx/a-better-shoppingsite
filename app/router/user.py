from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.model.database import get_db
from app.dependencies import get_current_user
from app.model.user import User
from app.model.cart import Cart

router = APIRouter(prefix="/api/user", tags=["user"])


class UserProfileResponse(BaseModel):
    success: bool = True
    data: Optional[dict] = None
    message: str = ""


class UpdateUserRequest(BaseModel):
    email: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    verification_code: str


class DeleteAccountRequest(BaseModel):
    password: str


@router.get("/me")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role_name,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    }


@router.put("/me")
async def update_user_profile(
    req: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.email:
        existing = db.query(User).filter(
            User.email == req.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = req.email
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role_name
        },
        "message": "User updated successfully"
    }


@router.put("/password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.service.auth_service import AuthService
    from app.service.email_service import EmailService
    
    if not AuthService.verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    if not EmailService.verify_code(db, current_user.email, req.verification_code, "change_password"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    current_user.password_hash = AuthService.hash_password(req.new_password)
    db.commit()
    
    return {"success": True, "message": "Password changed successfully"}


@router.delete("/me")
async def delete_account(
    req: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.service.auth_service import AuthService
    
    if not AuthService.verify_password(req.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    user_id = current_user.id
    deleted_marker = f"deleted_{user_id}_{int(db.query(func.current_timestamp()).first()[0].timestamp())}"
    
    current_user.username = deleted_marker
    current_user.email = None
    current_user.password_hash = None
    current_user.is_active = False
    
    db.query(Cart).filter(Cart.user_id == user_id).delete()
    
    db.commit()
    
    return {"success": True, "message": "Account deleted successfully"}