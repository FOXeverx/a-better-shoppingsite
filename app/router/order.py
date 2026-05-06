from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.model.database import get_db
from app.dependencies import get_current_user
from app.model.user import User
from app.model.order import OrderStatus
from app.service.order_service import OrderService

router = APIRouter(prefix="/api/order", tags=["order"])


class OrderCreateRequest(BaseModel):
    shipping_address: Optional[str] = None
    note: Optional[str] = None


class OrderResponse(BaseModel):
    success: bool = True
    data: Optional[dict] = None
    message: str = ""


class OrderListResponse(BaseModel):
    success: bool = True
    data: List[dict] = []
    pagination: Optional[dict] = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(
    req: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        order = OrderService.create_order(
            db=db,
            user_id=current_user.id,
            shipping_address=req.shipping_address,
            note=req.note
        )
        
        return OrderResponse(
            data={
                "id": order.id,
                "order_number": f"ORD{order.id:08d}",
                "status": order.status.value,
                "total_amount": float(order.total_amount),
                "confirm_token": order.confirm_token,
                "expires_at": order.expires_at.isoformat(),
                "created_at": order.created_at.isoformat()
            },
            message="Order created. Please confirm via email."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("")
async def get_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    status_enum = None
    if status_filter:
        try:
            status_enum = OrderStatus(status_filter)
        except ValueError:
            pass
    
    orders, total = OrderService.get_orders(
        db=db,
        user_id=current_user.id,
        status=status_enum,
        page=page,
        page_size=page_size
    )
    
    data = []
    for order in orders:
        items = [
            {
                "product_id": item.product_id,
                "product_name": item.product.name if item.product else "Unknown",
                "quantity": item.quantity,
                "price": float(item.price),
                "subtotal": float(item.price * item.quantity)
            }
            for item in order.items
        ]
        
        data.append({
            "id": order.id,
            "order_number": f"ORD{order.id:08d}",
            "status": order.status.value,
            "total_amount": float(order.total_amount),
            "items": items,
            "created_at": order.created_at.isoformat() if order.created_at else None
        })
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }
    }


@router.get("/confirm")
async def confirm_order(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        order = OrderService.confirm_order(db, token)
        return OrderResponse(
            data={"order_id": order.id, "status": order.status.value},
            message="Order confirmed successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = OrderService.get_order_by_id(db, order_id, current_user.id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    items = [
        {
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else "Unknown",
            "quantity": item.quantity,
            "price": float(item.price),
            "subtotal": float(item.price * item.quantity)
        }
        for item in order.items
    ]
    
    return OrderResponse(
        data={
            "id": order.id,
            "order_number": f"ORD{order.id:08d}",
            "status": order.status.value,
            "total_amount": float(order.total_amount),
            "shipping_address": order.shipping_address,
            "items": items,
            "confirmed_at": order.confirmed_at.isoformat() if order.confirmed_at else None,
            "created_at": order.created_at.isoformat() if order.created_at else None
        }
    )

@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        order = OrderService.cancel_order(db, order_id, current_user.id)
        return OrderResponse(
            data={"order_id": order.id, "status": order.status.value},
            message="Order cancelled"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )