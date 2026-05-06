from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.model.database import get_db
from app.dependencies import get_current_user
from app.model.user import User
from app.service.cart_service import CartService

router = APIRouter(prefix="/api/cart", tags=["cart"])


class CartAddRequest(BaseModel):
    product_id: int
    quantity: int = 1


class CartUpdateRequest(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    success: bool = True
    data: Optional[dict] = None
    message: str = ""


@router.get("")
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    summary = CartService.get_cart_summary(db, current_user.id)
    
    items = []
    for item in summary["items"]:
        if item.product and item.product.is_active:
            items.append({
                "id": item.id,
                "product": {
                    "id": item.product.id,
                    "name": item.product.name,
                    "price": float(item.product.price),
                    "image_url": item.product.image_url,
                    "stock": item.product.stock
                },
                "quantity": item.quantity,
                "subtotal": float(item.product.price * item.quantity)
            })
    
    return {
        "success": True,
        "data": items,
        "summary": {
            "total_items": summary["total_items"],
            "total_amount": float(summary["total_amount"])
        }
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    req: CartAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        cart_item = CartService.add_to_cart(
            db=db,
            user_id=current_user.id,
            product_id=req.product_id,
            quantity=req.quantity
        )
        
        return CartItemResponse(
            data={
                "id": cart_item.id,
                "product_id": cart_item.product_id,
                "quantity": cart_item.quantity
            },
            message="Added to cart successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{cart_id}")
async def update_cart_item(
    cart_id: int,
    req: CartUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        cart_item = CartService.update_cart_item(
            db=db,
            cart_id=cart_id,
            user_id=current_user.id,
            quantity=req.quantity
        )
        
        if not cart_item:
            return {"success": True, "message": "Item removed from cart"}
        
        return CartItemResponse(
            data={
                "id": cart_item.id,
                "product_id": cart_item.product_id,
                "quantity": cart_item.quantity
            },
            message="Cart updated successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{cart_id}")
async def remove_from_cart(
    cart_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = CartService.remove_from_cart(db, cart_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )
    
    return {"success": True, "message": "Item removed from cart"}


@router.delete("")
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    CartService.clear_cart(db, current_user.id)
    return {"success": True, "message": "Cart cleared"}