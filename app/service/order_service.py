from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.model.order import Order, OrderItem, OrderStatus
from app.model.cart import Cart
from app.model.product import Product
from app.model.user import User
from app.model.log import SalesStat
from app.service.auth_service import AuthService
import smtplib
from email.mime.text import MIMEText


class OrderService:
    ORDER_EXPIRE_HOURS = 24
    
    @staticmethod
    def create_order(
        db: Session,
        user_id: int,
        shipping_address: str = None,
        note: str = None,
        send_email: bool = True
    ) -> Order:
        cart_items = db.query(Cart).filter(Cart.user_id == user_id).all()
        
        if not cart_items:
            raise ValueError("Cart is empty")
        
        total_amount = Decimal("0")
        for item in cart_items:
            if item.product and item.product.is_active:
                total_amount += item.product.price * item.quantity
        
        if total_amount == 0:
            raise ValueError("Cart is empty")
        
        confirm_token = AuthService.create_confirm_token()
        expires_at = datetime.utcnow() + timedelta(hours=OrderService.ORDER_EXPIRE_HOURS)
        
        order = Order(
            user_id=user_id,
            status=OrderStatus.CREATED,
            total_amount=total_amount,
            confirm_token=confirm_token,
            shipping_address=shipping_address,
            note=note,
            expires_at=expires_at
        )
        db.add(order)
        db.flush()
        
        for item in cart_items:
            if item.product and item.product.is_active:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.product.price
                )
                db.add(order_item)
        
        for item in sorted(cart_items, key=lambda i: i.product_id):
            if item.product and item.product.is_active:
                product = db.query(Product).filter(
                    Product.id == item.product_id
                ).with_for_update().first()
                
                if not product or not product.is_active:
                    raise ValueError(f"Product {item.product.name} is no longer available")
                
                if product.stock < item.quantity:
                    raise ValueError(f"Insufficient stock for {product.name}")
                
                product.stock -= item.quantity
        
        db.query(Cart).filter(Cart.user_id == user_id).delete()
        
        db.commit()
        db.refresh(order)
        
        if send_email:
            OrderService._send_confirmation_email(db, order)
        
        return order
    
    @staticmethod
    def _send_confirmation_email(db: Session, order: Order):
        from app.config import get_config
        config = get_config()
        
        user = db.query(User).filter(User.id == order.user_id).first()
        if not user or not user.email:
            return
        
        confirm_url = f"{config.app.frontend_url}/order-confirmed?token={order.confirm_token}"
        
        subject = f"Order Confirmation - {order.id}"
        body = f"""
        <html>
        <body>
            <h2>Thank you for your order!</h2>
            <p>Your order #{order.id} has been created.</p>
            <p>Total Amount: ${order.total_amount}</p>
            <p>Please confirm your order by clicking the link below:</p>
            <p><a href="{confirm_url}">Confirm Order</a></p>
            <p>This link will expire in {OrderService.ORDER_EXPIRE_HOURS} hours.</p>
        </body>
        </html>
        """
        
        if not config.smtp.username or not config.smtp.password:
            print(f"[Email] Would send confirmation email to {user.email}")
            return
        
        try:
            msg = MIMEText(body, "html")
            msg["Subject"] = subject
            msg["From"] = config.smtp.username
            msg["To"] = user.email
            
            with smtplib.SMTP(config.smtp.host, config.smtp.port) as server:
                if config.smtp.use_tls:
                    server.starttls()
                server.login(config.smtp.username, config.smtp.password)
                server.send_message(msg)
        except Exception as e:
            print(f"[Email] Failed to send email: {e}")
    
    @staticmethod
    def confirm_order(
        db: Session,
        token: str
    ) -> Order:
        order = db.query(Order).filter(
            Order.confirm_token == token,
            Order.status == OrderStatus.CREATED
        ).with_for_update().first()
        
        if not order:
            raise ValueError("Invalid or already confirmed order")
        
        if order.expires_at < datetime.utcnow():
            for item in sorted(order.items, key=lambda i: i.product_id):
                product = db.query(Product).filter(
                    Product.id == item.product_id
                ).with_for_update().first()
                if product:
                    product.stock += item.quantity
            order.status = OrderStatus.CANCELLED
            db.commit()
            raise ValueError("Order has expired")
        
        order.status = OrderStatus.CONFIRMED
        order.confirmed_at = datetime.utcnow()
        order.confirm_token = None
        
        OrderService._update_sales_stat(db, order)
        db.commit()
        db.refresh(order)
        
        return order
    
    @staticmethod
    def _update_sales_stat(db: Session, order: Order):
        today = datetime.utcnow().date()
        
        stat = db.query(SalesStat).filter(
            func.date(SalesStat.stat_date) == today
        ).first()
        
        if stat:
            stat.total_amount += order.total_amount
            stat.order_count += 1
        else:
            stat = SalesStat(
                stat_date=datetime.utcnow(),
                total_amount=order.total_amount,
                order_count=1
            )
            db.add(stat)
        
        db.commit()
    
    @staticmethod
    def cancel_order(
        db: Session,
        order_id: int,
        user_id: int
    ) -> Order:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).first()
        
        if not order:
            raise ValueError("Order not found")
        
        if order.status != OrderStatus.CREATED:
            raise ValueError("Cannot cancel confirmed or cancelled order")
        
        for item in sorted(order.items, key=lambda i: i.product_id):
            product = db.query(Product).filter(
                Product.id == item.product_id
            ).with_for_update().first()
            if product:
                product.stock += item.quantity
        
        order.status = OrderStatus.CANCELLED
        db.commit()
        db.refresh(order)
        
        return order
    
    @staticmethod
    def get_orders(
        db: Session,
        user_id: int = None,
        status: OrderStatus = None,
        page: int = 1,
        page_size: int = 20
    ):
        query = db.query(Order)
        
        if user_id:
            query = query.filter(Order.user_id == user_id)
        
        if status:
            query = query.filter(Order.status == status)
        
        total = query.count()
        
        orders = query.order_by(Order.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return orders, total
    
    @staticmethod
    def get_order_by_id(
        db: Session,
        order_id: int,
        user_id: int = None
    ) -> Optional[Order]:
        query = db.query(Order).filter(Order.id == order_id)
        
        if user_id:
            query = query.filter(Order.user_id == user_id)
        
        return query.first()
    
    @staticmethod
    def cleanup_expired_orders(db: Session):
        orders = db.query(Order).filter(
            Order.status == OrderStatus.CREATED,
            Order.expires_at < datetime.utcnow()
        ).all()
        
        for order in orders:
            for item in sorted(order.items, key=lambda i: i.product_id):
                product = db.query(Product).filter(
                    Product.id == item.product_id
                ).with_for_update().first()
                if product:
                    product.stock += item.quantity
            order.status = OrderStatus.CANCELLED
        
        db.commit()
        return len(orders)