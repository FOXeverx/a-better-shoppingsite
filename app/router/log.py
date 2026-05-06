from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.model.database import get_db
from app.dependencies import get_current_user
from app.model.user import User
from app.service.log_service import LogService

router = APIRouter(prefix="/api/log", tags=["log"])


class BrowseLogRequest(BaseModel):
    product_id: int
    stay_time: int = 0


@router.post("/browse", status_code=status.HTTP_201_CREATED)
async def log_browse(
    req: BrowseLogRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    log = LogService.log_browse(
        db=db,
        user_id=current_user.id,
        product_id=req.product_id,
        stay_time=req.stay_time
    )
    
    return {
        "success": True,
        "message": "Browse log recorded",
        "log_id": log.id
    }


@router.get("/browse")
async def get_browse_logs(
    product_id: int = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logs = LogService.get_browse_logs(
        db=db,
        user_id=current_user.id,
        product_id=product_id,
        page=page,
        page_size=page_size
    )
    
    data = [
        {
            "id": log.id,
            "product_id": log.product_id,
            "stay_time": log.stay_time,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]
    
    return {"success": True, "data": data}