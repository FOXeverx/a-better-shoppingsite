from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.model.database import get_db
from app.service.auth_service import AuthService
from app.service.email_service import EmailService
from app.dependencies import get_current_user
from app.model.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    verification_code: str


class SendCodeRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    username: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    verification_code: str


class RegisterResponse(BaseModel):
    success: bool = True
    data: dict = None
    message: str = ""


class LoginResponse(BaseModel):
    success: bool = True
    data: dict = None
    message: str = ""


class SendCodeResponse(BaseModel):
    success: bool = True
    message: str = ""


@router.post("/send-verification-code", response_model=SendCodeResponse)
async def send_verification_code(
    request: Request,
    req: SendCodeRequest,
    db: Session = Depends(get_db)
):
    error, code = EmailService.send_verification_code(db, req.email, "register")
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    return SendCodeResponse(message="Verification code sent")


@router.post("/send-change-password-code", response_model=SendCodeResponse)
async def send_change_password_code(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    error, _ = EmailService.send_verification_code(db, current_user.email, "change_password")
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return SendCodeResponse(message="Verification code sent to your email")


@router.post("/register", response_model=RegisterResponse)
async def register(
    request: Request,
    req: RegisterRequest,
    db: Session = Depends(get_db)
):
    if req.password != req.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    # 验证验证码
    if not EmailService.verify_code(db, req.email, req.verification_code, "register"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    
    user, error = AuthService.register(
        db=db,
        username=req.username,
        email=req.email,
        password=req.password,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return RegisterResponse(
        data={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role_name,
            "created_at": user.created_at.isoformat()
        },
        message="Registration successful"
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    req: LoginRequest,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    
    user, error = AuthService.login(
        db=db,
        username=req.username,
        password=req.password,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )
    
    token = AuthService.create_access_token(user.id, user.role_name)
    
    return LoginResponse(
        data={
            "token": token,
            "token_type": "bearer",
            "expires_in": 86400,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role_name
            }
        },
        message="Login successful"
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    AuthService.logout(current_user, None)
    return {"success": True, "message": "Logout successful"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role_name,
            "is_active": current_user.is_active,
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
            "created_at": current_user.created_at.isoformat()
        }
    }


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    from app.model.user import User
    import secrets
    
    user = db.query(User).filter(
        (User.username == req.username) | (User.email == req.username)
    ).first()
    
    if not user:
        return {"success": True, "message": "If the account exists, a new password will be sent to the registered email"}
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is disabled")
    
    new_password = secrets.token_urlsafe(8)
    user.password_hash = AuthService.hash_password(new_password)
    db.commit()
    
    error, _ = EmailService.send_new_password(db, user.email, new_password)
    
    if error:
        raise HTTPException(status_code=500, detail=error)
    
    return {"success": True, "message": "If the account exists, a new password will be sent to the registered email"}


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not AuthService.verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    if not EmailService.verify_code(db, current_user.email, req.verification_code, "change_password"):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    
    current_user.password_hash = AuthService.hash_password(req.new_password)
    db.commit()
    
    return {"success": True, "message": "Password changed successfully"}