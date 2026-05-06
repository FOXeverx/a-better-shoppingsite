from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.model.database import get_db
from app.dependencies import get_current_user_optional, get_current_user
from app.model.user import User
from app.model.product import Product, RecommendItem
from app.model.order import Order, OrderItem
from app.model.log import BrowseLog

router = APIRouter(prefix="/api/recommend", tags=["recommend"])


class RecommendResponse(BaseModel):
    success: bool = True
    data: Optional[list] = None
    message: str = ""


@router.get("/product/{product_id}", response_model=RecommendResponse)
async def get_product_recommendations(
    product_id: int,
    limit: int = Query(5),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RecommendResponse(data=[])
    
    recommendations = db.query(RecommendItem).filter(
        RecommendItem.product_id == product_id
    ).order_by(RecommendItem.score.desc()).limit(limit).all()
    
    data = []
    for rec in recommendations:
        if rec.target_product and rec.target_product.is_active:
            data.append({
                "product_id": rec.target_product.id,
                "product_name": rec.target_product.name,
                "score": float(rec.score),
                "image_url": rec.target_product.image_url
            })
    
    return RecommendResponse(data=data)


@router.get("/bought-also/{product_id}", response_model=RecommendResponse)
async def get_bought_also_bought(
    product_id: int,
    limit: int = Query(5),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    from app.model.order import OrderStatus, Order
    from app.model.log import BrowseLog

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RecommendResponse(data=[])

    browsed_users_query = db.query(BrowseLog.user_id).filter(
        BrowseLog.product_id == product_id
    )

    if current_user:
        browsed_users_query = browsed_users_query.filter(
            BrowseLog.user_id != current_user.id
        )

    browsed_users = browsed_users_query.distinct().subquery()

    other_purchases = db.query(OrderItem).filter(
        OrderItem.order_id.in_(
            db.query(Order.id).filter(
                Order.user_id.in_(db.query(browsed_users)),
                Order.status == OrderStatus.CONFIRMED
            )
        ),
        OrderItem.product_id != product_id
    ).all()

    product_scores = {}
    for item in other_purchases:
        if item.product_id in product_scores:
            product_scores[item.product_id]['count'] += 1
        else:
            product_scores[item.product_id] = {'count': 1}

    if not product_scores:
        orders_with_product = db.query(OrderItem.order_id).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            OrderItem.product_id == product_id,
            Order.status == OrderStatus.CONFIRMED
        ).distinct().subquery()

        other_items = db.query(OrderItem).filter(
            OrderItem.order_id.in_(db.query(orders_with_product)),
            OrderItem.product_id != product_id
        ).all()

        for item in other_items:
            if item.product_id in product_scores:
                product_scores[item.product_id]['count'] += 1
            else:
                product_scores[item.product_id] = {'count': 1}

    sorted_products = sorted(
        product_scores.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )[:limit]

    data = []
    for prod_id, score_info in sorted_products:
        prod = db.query(Product).filter(Product.id == prod_id).first()
        if prod and prod.is_active:
            data.append({
                "product_id": prod.id,
                "product_name": prod.name,
                "score": score_info['count'],
                "image_url": prod.image_url,
                "reason": f"{score_info['count']}人购买"
            })

    if not data:
        return RecommendResponse(data=[])
    
    return RecommendResponse(data=data)


@router.get("/user/me", response_model=RecommendResponse)
async def get_user_recommendations(
    limit: int = Query(10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.model.log import BrowseLog
    from app.model.order import Order, OrderItem, OrderStatus
    from sqlalchemy import func

    user_role = current_user.role_name
    is_admin_or_sales = user_role in ["admin", "sales"]

    purchased_products = db.query(OrderItem.product_id).filter(
        OrderItem.order_id.in_(
            db.query(Order.id).filter(
                Order.user_id == current_user.id,
                Order.status == OrderStatus.CONFIRMED
            )
        )
    ).distinct().all()

    purchased_product_ids = set(p.product_id for p in purchased_products)

    if purchased_product_ids:
        recommendations = []
        for product_id in purchased_product_ids:
            recs = db.query(RecommendItem).filter(
                RecommendItem.product_id == product_id
            ).order_by(RecommendItem.score.desc()).limit(5).all()

            for rec in recs:
                if rec.target_product and rec.target_product.is_active:
                    if rec.target_product.id not in purchased_product_ids:
                        recommendations.append({
                            "product_id": rec.target_product.id,
                            "product_name": rec.target_product.name,
                            "score": float(rec.score),
                            "image_url": rec.target_product.image_url,
                            "reason": "Based on your purchases"
                        })

        seen = set()
        unique_recs = []
        for rec in recommendations:
            if rec["product_id"] not in seen:
                seen.add(rec["product_id"])
                unique_recs.append(rec)

        if unique_recs:
            return RecommendResponse(data=unique_recs[:limit])

    browse_logs = db.query(BrowseLog.product_id, func.count(BrowseLog.id).label("count")).filter(
        BrowseLog.user_id == current_user.id
    ).group_by(BrowseLog.product_id).order_by(func.count(BrowseLog.id).desc()).limit(5).all()

    if not browse_logs:
        if is_admin_or_sales:
            from app.model.order import Order, OrderItem, OrderStatus

            purchased_products = db.query(OrderItem.product_id).filter(
                OrderItem.order_id.in_(
                    db.query(Order.id).filter(
                        Order.user_id == current_user.id,
                        Order.status == OrderStatus.CONFIRMED
                    )
                )
            ).distinct().all()

            product_ids = [p.product_id for p in purchased_products]

            if product_ids:
                recommendations = []
                for product_id in product_ids:
                    recs = db.query(RecommendItem).filter(
                        RecommendItem.product_id == product_id
                    ).order_by(RecommendItem.score.desc()).limit(5).all()

                    for rec in recs:
                        if rec.target_product and rec.target_product.is_active:
                            recommendations.append({
                                "product_id": rec.target_product.id,
                                "product_name": rec.target_product.name,
                                "score": float(rec.score),
                                "image_url": rec.target_product.image_url,
                                "reason": "Based on your purchases"
                            })

                seen = set()
                unique_recs = []
                for rec in recommendations:
                    if rec["product_id"] not in seen:
                        seen.add(rec["product_id"])
                        unique_recs.append(rec)

                if unique_recs:
                    return RecommendResponse(data=unique_recs[:limit])

        popular_products = db.query(Product).filter(
            Product.is_active == True
        ).order_by(Product.created_at.desc()).limit(limit).all()

        return RecommendResponse(data=[
            {
                "product_id": p.id,
                "product_name": p.name,
                "score": 0.5,
                "reason": "热门商品"
            }
            for p in popular_products
        ])

    recommendations = []
    for log in browse_logs:
        recs = db.query(RecommendItem).filter(
            RecommendItem.product_id == log.product_id
        ).order_by(RecommendItem.score.desc()).limit(3).all()

        for rec in recs:
            if rec.target_product and rec.target_product.is_active:
                recommendations.append({
                    "product_id": rec.target_product.id,
                    "product_name": rec.target_product.name,
                    "score": float(rec.score),
                    "image_url": rec.target_product.image_url,
                    "reason": "Based on your browsing history"
                })

    seen = set()
    unique_recs = []
    for rec in recommendations:
        if rec["product_id"] not in seen:
            seen.add(rec["product_id"])
            unique_recs.append(rec)

    if not unique_recs:
        popular_products = db.query(Product).filter(
            Product.is_active == True
        ).order_by(Product.created_at.desc()).limit(limit).all()

        return RecommendResponse(data=[
            {
                "product_id": p.id,
                "product_name": p.name,
                "score": 0.5,
                "reason": "热门商品"
            }
            for p in popular_products
        ])

    return RecommendResponse(data=unique_recs[:limit])