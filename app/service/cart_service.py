from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from app.model.cart import Cart
from app.model.product import Product
from app.model.user import User


class CartService:
    @staticmethod
    def get_cart_items(db: Session, user_id: int) -> List[Cart]:
        return db.query(Cart).filter(Cart.user_id == user_id).all()
    
    @staticmethod
    def get_cart_summary(db: Session, user_id: int) -> Dict[str, Any]:
        items = CartService.get_cart_items(db, user_id)
        total_amount = Decimal("0")
        total_items = 0
        
        for item in items:
            if item.product and item.product.is_active:
                subtotal = item.product.price * item.quantity
                total_amount += subtotal
                total_items += item.quantity
        
        return {
            "items": items,
            "total_items": total_items,
            "total_amount": total_amount
        }
    
    @staticmethod
    def add_to_cart(
        db: Session,
        user_id: int,
        product_id: int,
        quantity: int = 1
    ) -> Cart:
        product = db.query(Product).filter(
            Product.id == product_id,
            Product.is_active == True
        ).first()
        
        if not product:
            raise ValueError("Product not found")
        
        if product.stock < quantity:
            raise ValueError("Insufficient stock")
        
        cart_item = db.query(Cart).filter(
            Cart.user_id == user_id,
            Cart.product_id == product_id
        ).first()
        
        if cart_item:
            new_quantity = cart_item.quantity + quantity
            if product.stock < new_quantity:
                raise ValueError("Insufficient stock")
            cart_item.quantity = new_quantity
        else:
            cart_item = Cart(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity
            )
            db.add(cart_item)
        
        db.commit()
        db.refresh(cart_item)
        return cart_item
    
    @staticmethod
    def update_cart_item(
        db: Session,
        cart_id: int,
        user_id: int,
        quantity: int
    ) -> Cart:
        cart_item = db.query(Cart).filter(
            Cart.id == cart_id,
            Cart.user_id == user_id
        ).first()
        
        if not cart_item:
            raise ValueError("Cart item not found")
        
        if quantity <= 0:
            db.delete(cart_item)
            db.commit()
            return None
        
        if cart_item.product and cart_item.product.stock < quantity:
            raise ValueError("Insufficient stock")
        
        cart_item.quantity = quantity
        db.commit()
        db.refresh(cart_item)
        return cart_item
    
    @staticmethod
    def remove_from_cart(
        db: Session,
        cart_id: int,
        user_id: int
    ) -> bool:
        cart_item = db.query(Cart).filter(
            Cart.id == cart_id,
            Cart.user_id == user_id
        ).first()
        
        if not cart_item:
            return False
        
        db.delete(cart_item)
        db.commit()
        return True
    
    @staticmethod
    def clear_cart(db: Session, user_id: int) -> bool:
        db.query(Cart).filter(Cart.user_id == user_id).delete()
        db.commit()
        return True