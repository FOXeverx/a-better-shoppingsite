from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.model.database import get_db
from app.dependencies import require_role, get_current_user
from app.model.user import User
from app.model.product import Product
from app.service.user_service import UserService
from app.service.product_service import ProductService
from app.service.log_service import LogService, AdminService
from app.service.order_service import OrderService

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
async def get_stats(
    period: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    start = None
    end = None
    if start_date:
        start = datetime.fromisoformat(start_date)
    if end_date:
        end = datetime.fromisoformat(end_date) + timedelta(days=1) - timedelta(seconds=1)
    stats = AdminService.get_dashboard_stats(db, period=period, start_date=start, end_date=end)
    return {"success": True, "data": stats}


@router.get("/stats/trend")
async def get_sales_trend(
    days: int = Query(7),
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    trend = AdminService.get_sales_trend(db, days)
    return {"success": True, "data": trend}


@router.get("/users")
async def get_users(
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    users = UserService.get_users(
        db=db,
        role=role,
        is_active=is_active,
        page=page,
        page_size=page_size
    )
    
    data = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role_name,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]
    
    return {"success": True, "data": data}


@router.get("/users/simple")
async def get_users_simple(
    search: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.contains(search)) | 
            (User.email.contains(search))
        )
    
    total = query.count()
    users = query.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    data = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role_name,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]
    
    return {"success": True, "data": data, "pagination": {"page": page, "page_size": page_size, "total": total}}


@router.get("/user/{user_id}/browse")
async def get_user_browse_logs(
    user_id: int,
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    from app.model.log import BrowseLog
    from app.model.product import Product
    
    query = db.query(BrowseLog).filter(BrowseLog.user_id == user_id)
    total = query.count()
    logs = query.order_by(BrowseLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    data = []
    for log in logs:
        product = db.query(Product).filter(Product.id == log.product_id).first()
        data.append({
            "id": log.id,
            "product_id": log.product_id,
            "product_name": product.name if product else "未知商品",
            "stay_time": log.stay_time or 0,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    return {"success": True, "data": data, "pagination": {"page": page, "page_size": page_size, "total": total}}


@router.get("/user/{user_id}/logins")
async def get_user_login_logs(
    user_id: int,
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    from app.model.log import LoginLog
    
    query = db.query(LoginLog).filter(LoginLog.user_id == user_id)
    total = query.count()
    logs = query.order_by(LoginLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    data = [
        {
            "id": log.id,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "success": log.success,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]
    
    return {"success": True, "data": data, "pagination": {"page": page, "page_size": page_size, "total": total}}


@router.get("/user/{user_id}/purchases/summary")
async def get_user_purchase_summary(
    user_id: int,
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    from app.model.order import Order, OrderItem
    from app.model.product import Product, Category
    
    orders = db.query(Order).filter(Order.user_id == user_id, Order.status == "CONFIRMED").all()
    
    category_stats = {}
    for order in orders:
        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product or not product.category_id:
                continue
            
            cat_id = product.category_id
            if cat_id not in category_stats:
                category = db.query(Category).filter(Category.id == cat_id).first()
                category_stats[cat_id] = {
                    "category_id": cat_id,
                    "category_name": category.name if category else "未分类",
                    "total_quantity": 0,
                    "total_amount": 0
                }
            
            category_stats[cat_id]["total_quantity"] += item.quantity
            category_stats[cat_id]["total_amount"] += float(item.price) * item.quantity
    
    data = list(category_stats.values())
    data.sort(key=lambda x: x["total_amount"], reverse=True)
    
    return {"success": True, "data": data}


@router.get("/user/{user_id}/purchases/{category_id}")
async def get_user_purchase_by_category(
    user_id: int,
    category_id: int,
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    from app.model.order import Order, OrderItem
    from app.model.product import Product
    
    orders = db.query(Order).filter(Order.user_id == user_id, Order.status == "CONFIRMED").all()
    
    order_ids = [o.id for o in orders]
    query = db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids), OrderItem.product_id.in_(
        db.query(Product.id).filter(Product.category_id == category_id)
    ))
    
    total = query.count()
    items = query.order_by(OrderItem.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    data = []
    for item in items:
        order = db.query(Order).filter(Order.id == item.order_id).first()
        product = db.query(Product).filter(Product.id == item.product_id).first()
        data.append({
            "order_id": order.id if order else None,
            "order_number": order.order_number if order else None,
            "created_at": order.created_at.isoformat() if order and order.created_at else None,
            "product_id": item.product_id,
            "product_name": product.name if product else "未知商品",
            "quantity": item.quantity,
            "price": float(item.price),
            "subtotal": float(item.price) * item.quantity
        })
    
    return {"success": True, "data": data, "pagination": {"page": page, "page_size": page_size, "total": total}}


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    profile = UserService.get_user_profile(db, user_id)
    
    return {
        "success": True,
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role_name,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "profile": {
                "activity_score": profile.activity_score if profile else 0,
                "spending_level": profile.spending_level.value if profile else "low"
            }
        }
    }


class UserCreateRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "customer"


@router.post("/user", status_code=status.HTTP_201_CREATED)
async def create_user(
    req: UserCreateRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    try:
        user = UserService.create_user(
            db=db,
            username=req.username,
            email=req.email,
            password=req.password,
            role_name=req.role,
            created_by=current_user.id
        )
        
        return {
            "success": True,
            "data": {
                "id": user.id,
                "username": user.username,
                "role": user.role_name
            },
            "message": "User created successfully"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/user/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    success = UserService.deactivate_user(db, user_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"success": True, "message": "User deactivated"}


@router.get("/logs")
async def get_operation_logs(
    action: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from app.model.user import User as UserModel
    
    logs = LogService.get_operation_logs(
        db=db,
        action=action,
        page=page,
        page_size=page_size
    )
    
    data = []
    for log in logs:
        user = db.query(UserModel).filter(UserModel.id == log.user_id).first()
        data.append({
            "id": log.id,
            "user_id": log.user_id,
            "username": user.username if user else "Unknown",
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    return {"success": True, "data": data}


@router.get("/logs/login")
async def get_login_logs(
    user_id: Optional[int] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(require_role("admin", "sales")),
    db: Session = Depends(get_db)
):
    logs = LogService.get_login_logs(
        db=db,
        user_id=user_id,
        page=page,
        page_size=page_size
    )
    
    data = []
    for log in logs:
        data.append({
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username,
            "ip_address": log.ip_address,
            "success": log.success,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    return {"success": True, "data": data}


@router.get("/logs/browse")
async def get_all_browse_logs(
    product_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(require_role("admin", "sales")),
    db: Session = Depends(get_db)
):
    from app.model.log import BrowseLog
    
    query = db.query(BrowseLog)
    
    if product_id:
        query = query.filter(BrowseLog.product_id == product_id)
    if user_id:
        query = query.filter(BrowseLog.user_id == user_id)
    
    total = query.count()
    logs = query.order_by(BrowseLog.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    from app.model.product import Product
    from app.model.user import User as UserModel
    
    data = []
    for log in logs:
        product = db.query(Product).filter(Product.id == log.product_id).first()
        user = db.query(UserModel).filter(UserModel.id == log.user_id).first()
        data.append({
            "id": log.id,
            "user_id": log.user_id,
            "username": user.username if user else "Unknown",
            "product_id": log.product_id,
            "product_name": product.name if product else "Unknown",
            "stay_time": log.stay_time,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total
        }
    }


@router.get("/anomalies")
async def get_anomalies(
    is_resolved: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    anomalies = LogService.get_anomaly_logs(
        db=db,
        is_resolved=is_resolved,
        severity=severity,
        page=page,
        page_size=page_size
    )
    
    data = []
    for a in anomalies:
        data.append({
            "id": a.id,
            "anomaly_type": a.anomaly_type,
            "description": a.description,
            "severity": a.severity.value,
            "is_resolved": a.is_resolved,
            "created_at": a.created_at.isoformat() if a.created_at else None
        })
    
    return {"success": True, "data": data}


@router.post("/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly(
    anomaly_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    success = LogService.resolve_anomaly(db, anomaly_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anomaly not found"
        )
    return {"success": True, "message": "Anomaly resolved"}


@router.post("/recommend/trigger")
async def trigger_recommend(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from scripts.recommend import CooccurrenceRecommender, CollaborativeFilter

    try:
        cooccurrence = CooccurrenceRecommender(db)
        cooccurrence_count = cooccurrence.run()

        collaborative = CollaborativeFilter(db)
        collaborative.run()

        return {
            "success": True,
            "message": f"Recommendation completed: {cooccurrence_count} items created",
            "data": {
                "cooccurrence_items": cooccurrence_count
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(e)}"
        )


@router.get("/sales")
async def get_sales_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    start = None
    end = None
    
    if start_date:
        start = datetime.fromisoformat(start_date)
    if end_date:
        end = datetime.fromisoformat(end_date) + timedelta(days=1) - timedelta(seconds=1)
    
    stats = LogService.get_sales_stats(db, start, end)
    
    data = [
        {
            "date": s.stat_date.isoformat() if s.stat_date else None,
            "amount": float(s.total_amount),
            "orders": s.order_count,
            "users": s.user_count
        }
        for s in stats
    ]
    
    return {"success": True, "data": data}


@router.get("/product-sales")
async def get_product_sales(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10),
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    from app.model.order import OrderItem, Order, OrderStatus
    from sqlalchemy import func
    
    start = None
    end = None
    
    if start_date:
        start = datetime.fromisoformat(start_date)
    if end_date:
        end = datetime.fromisoformat(end_date) + timedelta(days=1) - timedelta(seconds=1)
    
    query = db.query(
        OrderItem.product_id,
        Product.name,
        func.sum(OrderItem.quantity).label('quantity'),
        func.sum(OrderItem.price * OrderItem.quantity).label('revenue'),
        func.count(OrderItem.order_id).label('order_count')
    ).join(Order, OrderItem.order_id == Order.id).join(Product, OrderItem.product_id == Product.id).filter(
        Order.status == OrderStatus.CONFIRMED
    )
    
    if start:
        query = query.filter(Order.created_at >= start)
    if end:
        query = query.filter(Order.created_at <= end)
    
    results = query.group_by(OrderItem.product_id, Product.name).order_by(
        func.sum(OrderItem.price * OrderItem.quantity).desc()
    ).limit(limit).all()
    
    data = [
        {
            "product_id": r.product_id,
            "product_name": r.name,
            "quantity": r.quantity,
            "revenue": float(r.revenue),
            "order_count": r.order_count
        }
        for r in results
    ]
    
    return {"success": True, "data": data}


@router.get("/order/{order_id}")
async def get_order_detail(
    order_id: int,
    current_user: User = Depends(require_role("admin", "sales")),
    db: Session = Depends(get_db)
):
    from app.model.order import Order
    
    order = db.query(Order).filter(Order.id == order_id).first()
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
    
    user = db.query(User).filter(User.id == order.user_id).first()
    
    return {
        "success": True,
        "data": {
            "id": order.id,
            "order_number": f"ORD{order.id:08d}",
            "user_id": order.user_id,
            "username": user.username if user else "Unknown",
            "status": order.status.value,
            "total_amount": float(order.total_amount),
            "shipping_address": order.shipping_address,
            "note": order.note,
            "items": items,
            "confirmed_at": order.confirmed_at.isoformat() if order.confirmed_at else None,
            "created_at": order.created_at.isoformat() if order.created_at else None
        }
    }


@router.get("/orders")
async def get_all_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(require_role("admin", "sales")),
    db: Session = Depends(get_db)
):
    from app.model.order import Order, OrderStatus
    
    status_enum = None
    if status_filter:
        try:
            status_enum = OrderStatus(status_filter)
        except ValueError:
            pass
    
    query = db.query(Order)
    
    if status_enum:
        query = query.filter(Order.status == status_enum)
    
    total = query.count()
    
    orders = query.order_by(Order.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    data = []
    for order in orders:
        user = db.query(User).filter(User.id == order.user_id).first()
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
            "user_id": order.user_id,
            "username": user.username if user else "Unknown",
            "status": order.status.value,
            "total_amount": float(order.total_amount),
            "shipping_address": order.shipping_address,
            "items": items,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "confirmed_at": order.confirmed_at.isoformat() if order.confirmed_at else None
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


@router.put("/order/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: str = Query(...),
    current_user: User = Depends(require_role("admin", "sales")),
    db: Session = Depends(get_db)
):
    from app.model.order import Order, OrderStatus
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    try:
        new_status = OrderStatus(status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status"
        )
    
    old_status = order.status
    order.status = new_status
    
    if new_status == OrderStatus.CONFIRMED and not order.confirmed_at:
        if old_status != OrderStatus.CREATED:
            for item in sorted(order.items, key=lambda i: i.product_id):
                product = db.query(Product).filter(
                    Product.id == item.product_id
                ).with_for_update().first()
                if not product or not product.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product {item.product_id} is no longer available"
                    )
                if product.stock < item.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient stock for product {item.product_id}"
                    )
                product.stock -= item.quantity
        order.confirmed_at = datetime.utcnow()
    
    elif new_status == OrderStatus.CANCELLED:
        if old_status in (OrderStatus.CREATED, OrderStatus.CONFIRMED):
            for item in sorted(order.items, key=lambda i: i.product_id):
                product = db.query(Product).filter(
                    Product.id == item.product_id
                ).with_for_update().first()
                if product:
                    product.stock += item.quantity
    
    db.commit()
    db.refresh(order)
    
    return {
        "success": True,
        "data": {
            "id": order.id,
            "status": order.status.value
        },
        "message": "Order status updated"
    }


@router.delete("/order/{order_id}")
async def delete_order(
    order_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from app.model.order import Order
    from app.model.product import Product
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status in (OrderStatus.CREATED, OrderStatus.CONFIRMED):
        for item in sorted(order.items, key=lambda i: i.product_id):
            product = db.query(Product).filter(
                Product.id == item.product_id
            ).with_for_update().first()
            if product:
                product.stock += item.quantity
    
    db.delete(order)
    db.commit()
    
    return {
        "success": True,
        "message": "Order deleted"
    }


@router.get("/user-stats")
async def get_user_stats(
    current_user: User = Depends(require_role("admin", "sales")),
    db: Session = Depends(get_db)
):
    from app.model.user import UserProfile, SpendingLevel
    from sqlalchemy import func
    
    total = db.query(UserProfile).count()
    
    spending_dist = {
        "low": db.query(UserProfile).filter(UserProfile.spending_level == SpendingLevel.LOW).count(),
        "medium": db.query(UserProfile).filter(UserProfile.spending_level == SpendingLevel.MEDIUM).count(),
        "high": db.query(UserProfile).filter(UserProfile.spending_level == SpendingLevel.HIGH).count(),
    }
    
    avg_spent = db.query(func.avg(UserProfile.total_spent)).scalar() or 0
    avg_orders = db.query(func.avg(UserProfile.order_count)).scalar() or 0
    
    region_dist = {}
    profiles = db.query(UserProfile).all()
    for p in profiles:
        r = p.region or "未知"
        region_dist[r] = region_dist.get(r, 0) + 1
    
    return {
        "success": True,
        "data": {
            "total_users": total,
            "spending_distribution": spending_dist,
            "avg_spent": float(avg_spent),
            "avg_orders": float(avg_orders),
            "region_distribution": region_dist
        }
    }


@router.get("/anomaly-stats")
async def get_anomaly_stats(
    current_user: User = Depends(require_role("admin", "sales")),
    db: Session = Depends(get_db)
):
    from app.model.log import AnomalyLog, AnomalySeverity
    from datetime import timedelta
    
    total = db.query(AnomalyLog).count()
    unresolved = db.query(AnomalyLog).filter(AnomalyLog.is_resolved == False).count()
    
    by_severity = {
        "high": db.query(AnomalyLog).filter(AnomalyLog.severity == AnomalySeverity.HIGH, AnomalyLog.is_resolved == False).count(),
        "medium": db.query(AnomalyLog).filter(AnomalyLog.severity == AnomalySeverity.MEDIUM, AnomalyLog.is_resolved == False).count(),
        "low": db.query(AnomalyLog).filter(AnomalyLog.severity == AnomalySeverity.LOW, AnomalyLog.is_resolved == False).count(),
    }
    
    recent = db.query(AnomalyLog).filter(AnomalyLog.created_at > datetime.utcnow() - timedelta(hours=24)).count()
    
    return {
        "success": True,
        "data": {
            "total": total,
            "unresolved": unresolved,
            "by_severity": by_severity,
            "last_24h": recent
        }
    }


@router.post("/anomaly/{id}/resolve")
async def resolve_anomaly(
    id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from app.model.log import AnomalyLog
    
    anomaly = db.query(AnomalyLog).filter(AnomalyLog.id == id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    anomaly.is_resolved = True
    anomaly.resolved_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "Anomaly resolved"}


@router.get("/sales-predict")
async def get_sales_prediction(
    days: int = Query(7),
    current_user: User = Depends(require_role("admin", "sales")),
    db: Session = Depends(get_db)
):
    from app.model.log import SalesStat
    
    stats = db.query(SalesStat).order_by(SalesStat.stat_date.desc()).limit(30).all()
    
    if len(stats) < 7:
        return {"success": True, "data": {"trend": "insufficient_data", "message": "数据不足，无法预测"}}
    
    amounts = [float(s.total_amount) for s in stats[:7]]
    avg = sum(amounts) / len(amounts)
    
    trend = "stable"
    if amounts[-1] > amounts[0] * 1.2:
        trend = "increasing"
    elif amounts[-1] < amounts[0] * 0.8:
        trend = "decreasing"
    
    return {
        "success": True,
        "data": {
            "trend": trend,
            "current_avg": avg,
            "prediction": avg * 1.05 if trend == "increasing" else (avg * 0.95 if trend == "decreasing" else avg),
            "confidence": min(100, len(stats) * 3),
            "recent_data": [{"date": s.stat_date.isoformat(), "amount": float(s.total_amount)} for s in stats[:7]]
        }
    }


# ============ 安全威胁相关 API ============

@router.get("/security/threats")
async def get_security_threats(
    threat_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from app.model.log import SecurityThreat, ThreatType, ThreatSeverity
    
    query = db.query(SecurityThreat)
    
    if threat_type:
        query = query.filter(SecurityThreat.threat_type == threat_type)
    if severity:
        query = query.filter(SecurityThreat.severity == severity)
    if is_resolved is not None:
        query = query.filter(SecurityThreat.is_resolved == is_resolved)
    
    total = query.count()
    threats = query.order_by(SecurityThreat.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    data = [
        {
            "id": t.id,
            "threat_type": t.threat_type.value if t.threat_type else t.threat_type,
            "ip_address": t.ip_address,
            "user_agent": t.user_agent,
            "details": t.details,
            "severity": t.severity.value if t.severity else t.severity,
            "is_resolved": t.is_resolved,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None
        }
        for t in threats
    ]
    
    return {"success": True, "data": data, "pagination": {"page": page, "page_size": page_size, "total": total}}


@router.post("/security/threats/{threat_id}/resolve")
async def resolve_threat(
    threat_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from app.model.log import SecurityThreat
    
    threat = db.query(SecurityThreat).filter(SecurityThreat.id == threat_id).first()
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    threat.is_resolved = True
    threat.resolved_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "Threat resolved"}


@router.get("/security/threats/stats")
async def get_threat_stats(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from app.model.log import SecurityThreat, ThreatSeverity
    
    total = db.query(SecurityThreat).count()
    unresolved = db.query(SecurityThreat).filter(SecurityThreat.is_resolved == False).count()
    high_critical = db.query(SecurityThreat).filter(
        SecurityThreat.severity.in_([ThreatSeverity.HIGH, ThreatSeverity.CRITICAL])
    ).filter(SecurityThreat.is_resolved == False).count()
    
    from datetime import timedelta
    today = datetime.utcnow() - timedelta(days=1)
    today_count = db.query(SecurityThreat).filter(SecurityThreat.created_at >= today).count()
    
    return {
        "success": True,
        "data": {
            "total": total,
            "unresolved": unresolved,
            "high_critical": high_critical,
            "today": today_count
        }
    }


@router.get("/security/ip-blocks")
async def get_ip_blocks(
    page: int = Query(1),
    page_size: int = Query(20),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from app.model.log import IPBlock
    
    total = db.query(IPBlock).count()
    blocks = db.query(IPBlock).order_by(IPBlock.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    data = [
        {
            "id": b.id,
            "ip_address": b.ip_address,
            "block_type": b.block_type.value if b.block_type else b.block_type,
            "reason": b.reason,
            "expires_at": b.expires_at.isoformat() if b.expires_at else None,
            "created_by_id": b.created_by_id,
            "created_at": b.created_at.isoformat() if b.created_at else None
        }
        for b in blocks
    ]
    
    return {"success": True, "data": data, "pagination": {"page": page, "page_size": page_size, "total": total}}


class IPBlockRequest(BaseModel):
    ip_address: str
    reason: Optional[str] = None
    expires_minutes: Optional[int] = None  # None 表示永久封禁


@router.post("/security/ip-blocks")
async def create_ip_block(
    req: IPBlockRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from app.model.log import IPBlock, BlockType
    from datetime import timedelta
    
    expires_at = None
    if req.expires_minutes:
        expires_at = datetime.utcnow() + timedelta(minutes=req.expires_minutes)
    
    existing = db.query(IPBlock).filter(IPBlock.ip_address == req.ip_address).first()
    if existing:
        existing.block_type = BlockType.MANUAL
        existing.reason = req.reason
        existing.expires_at = expires_at
        existing.created_by_id = current_user.id
    else:
        ip_block = IPBlock(
            ip_address=req.ip_address,
            block_type=BlockType.MANUAL,
            reason=req.reason,
            expires_at=expires_at,
            created_by_id=current_user.id
        )
        db.add(ip_block)
    
    db.commit()
    
    return {"success": True, "message": "IP blocked"}


@router.delete("/security/ip-blocks/{block_id}")
async def unblock_ip(
    block_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from app.model.log import IPBlock
    
    block = db.query(IPBlock).filter(IPBlock.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="IP block not found")
    
    db.delete(block)
    db.commit()
    
    return {"success": True, "message": "IP unblocked"}