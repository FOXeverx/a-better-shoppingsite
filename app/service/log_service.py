from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.model.log import LoginLog, BrowseLog, OperationLog, SalesStat, AnomalyLog
from app.model.user import User
from app.model.product import Product


class LogService:
    @staticmethod
    def log_browse(
        db: Session,
        user_id: int,
        product_id: int,
        stay_time: int = 0
    ) -> BrowseLog:
        browse_log = BrowseLog(
            user_id=user_id,
            product_id=product_id,
            stay_time=stay_time
        )
        db.add(browse_log)
        db.commit()
        return browse_log
    
    @staticmethod
    def get_browse_logs(
        db: Session,
        user_id: int = None,
        product_id: int = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[BrowseLog]:
        query = db.query(BrowseLog)
        
        if user_id:
            query = query.filter(BrowseLog.user_id == user_id)
        if product_id:
            query = query.filter(BrowseLog.product_id == product_id)
        
        return query.order_by(BrowseLog.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
    
    @staticmethod
    def get_login_logs(
        db: Session,
        user_id: int = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[LoginLog]:
        query = db.query(LoginLog)
        
        if user_id:
            query = query.filter(LoginLog.user_id == user_id)
        
        return query.order_by(LoginLog.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
    
    @staticmethod
    def get_operation_logs(
        db: Session,
        user_id: int = None,
        action: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[OperationLog]:
        query = db.query(OperationLog)
        
        if user_id:
            query = query.filter(OperationLog.user_id == user_id)
        if action:
            query = query.filter(OperationLog.action == action)
        
        return query.order_by(OperationLog.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
    
    @staticmethod
    def get_sales_stats(
        db: Session,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[SalesStat]:
        query = db.query(SalesStat)
        
        if start_date:
            query = query.filter(SalesStat.stat_date >= start_date)
        if end_date:
            query = query.filter(SalesStat.stat_date <= end_date)
        
        return query.order_by(SalesStat.stat_date.desc()).all()
    
    @staticmethod
    def get_anomaly_logs(
        db: Session,
        is_resolved: bool = None,
        severity: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[AnomalyLog]:
        query = db.query(AnomalyLog)
        
        if is_resolved is not None:
            query = query.filter(AnomalyLog.is_resolved == is_resolved)
        if severity:
            query = query.filter(AnomalyLog.severity == severity)
        
        return query.order_by(AnomalyLog.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
    
    @staticmethod
    def create_anomaly(
        db: Session,
        anomaly_type: str,
        description: str,
        severity: str = "medium",
        details: dict = None
    ) -> AnomalyLog:
        import json
        anomaly = AnomalyLog(
            anomaly_type=anomaly_type,
            description=description,
            severity=severity,
            details=json.dumps(details) if details else None
        )
        db.add(anomaly)
        db.commit()
        return anomaly
    
    @staticmethod
    def resolve_anomaly(
        db: Session,
        anomaly_id: int
    ) -> bool:
        anomaly = db.query(AnomalyLog).filter(AnomalyLog.id == anomaly_id).first()
        if not anomaly:
            return False
        anomaly.is_resolved = True
        anomaly.resolved_at = datetime.utcnow()
        db.commit()
        return True


def _get_orders_in_range(db, start_date, end_date):
    from app.model.order import Order, OrderStatus

    query = db.query(Order).filter(Order.status == OrderStatus.CONFIRMED)
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)
    return query.order_by(Order.created_at.asc()).all()


def _get_daily_trend(db, start_date, end_date):
    if not start_date and not end_date:
        start_date = datetime.utcnow() - timedelta(days=30)

    orders = _get_orders_in_range(db, start_date, end_date)
    groups = {}
    for o in orders:
        day = o.created_at.date().isoformat() if o.created_at else None
        if day is None:
            continue
        if day not in groups:
            groups[day] = {"date": day, "orders": 0, "amount": 0.0}
        groups[day]["orders"] += 1
        groups[day]["amount"] += float(o.total_amount)
    return sorted(groups.values(), key=lambda x: x["date"])


def _get_weekly_trend(db, start_date, end_date):
    if not start_date and not end_date:
        start_date = datetime.utcnow() - timedelta(weeks=12)

    orders = _get_orders_in_range(db, start_date, end_date)
    groups = {}
    for o in orders:
        if not o.created_at:
            continue
        iso = o.created_at.isocalendar()
        week_key = f"{iso[0]}-W{iso[1]:02d}"
        if week_key not in groups:
            groups[week_key] = {"date": week_key, "orders": 0, "amount": 0.0}
        groups[week_key]["orders"] += 1
        groups[week_key]["amount"] += float(o.total_amount)
    return sorted(groups.values(), key=lambda x: x["date"])


def _get_monthly_trend(db, start_date, end_date):
    if not start_date and not end_date:
        start_date = datetime.utcnow() - timedelta(days=365)

    orders = _get_orders_in_range(db, start_date, end_date)
    groups = {}
    for o in orders:
        if not o.created_at:
            continue
        month_key = o.created_at.strftime("%Y-%m")
        if month_key not in groups:
            groups[month_key] = {"date": month_key, "orders": 0, "amount": 0.0}
        groups[month_key]["orders"] += 1
        groups[month_key]["amount"] += float(o.total_amount)
    return sorted(groups.values(), key=lambda x: x["date"])


class AdminService:
    @staticmethod
    def get_dashboard_stats(
        db: Session,
        period: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> dict:
        from app.model.user import User
        from app.model.product import Product
        from app.model.order import Order, OrderStatus
        
        total_users = db.query(User).count()
        total_products = db.query(Product).filter(Product.is_active == True).count()
        
        order_query = db.query(Order).filter(Order.status == OrderStatus.CONFIRMED)
        
        if start_date:
            order_query = order_query.filter(Order.created_at >= start_date)
        if end_date:
            order_query = order_query.filter(Order.created_at <= end_date)
        
        all_confirmed_orders = order_query.all()
        total_amount = sum(o.total_amount for o in all_confirmed_orders)
        total_orders = len(all_confirmed_orders)
        
        if period == "weekly":
            trend_data = _get_weekly_trend(db, start_date, end_date)
        elif period == "monthly":
            trend_data = _get_monthly_trend(db, start_date, end_date)
        else:
            trend_data = _get_daily_trend(db, start_date, end_date)
        
        return {
            "total_users": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_amount": float(total_amount),
            "trend": trend_data
        }
    
    @staticmethod
    def get_sales_trend(
        db: Session,
        days: int = 7
    ) -> List[dict]:
        start_date = datetime.utcnow() - timedelta(days=days)
        stats = db.query(SalesStat).filter(
            SalesStat.stat_date >= start_date
        ).order_by(SalesStat.stat_date).all()
        
        return [
            {
                "date": s.stat_date,
                "amount": float(s.total_amount),
                "orders": s.order_count
            }
            for s in stats
        ]