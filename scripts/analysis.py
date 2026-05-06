"""
Data Analysis Script
- User profile analysis (region, spending power, preference)
- Sales trend analysis
- Product ranking
- Anomaly detection
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from decimal import Decimal
import json
from collections import defaultdict, Counter

# Import all models to ensure they are registered
from app.model.user import User, UserProfile, Role
from app.model.product import Product, Category
from app.model.cart import Cart
from app.model.order import Order, OrderItem, OrderStatus
from app.model.log import LoginLog, BrowseLog, OperationLog, SalesStat, AnomalyLog


class UserProfiler:
    def __init__(self, db):
        self.db = db
    
    def analyze_user(self, user_id):
        from app.model.user import User, UserProfile
        from app.model.order import Order, OrderStatus
        from app.model.log import BrowseLog
        from sqlalchemy import func
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or user.role_name in ('admin', 'sales'):
            return None
        
        total_spent = self.db.query(func.sum(Order.total_amount)).filter(
            Order.user_id == user_id,
            Order.status == OrderStatus.CONFIRMED
        ).scalar() or 0
        
        order_count = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.status == OrderStatus.CONFIRMED
        ).count()
        
        avg_order_amount = float(total_spent) / order_count if order_count > 0 else 0
        
        browse_logs = self.db.query(BrowseLog).filter(
            BrowseLog.user_id == user_id
        ).all()
        
        category_counter = Counter()
        for log in browse_logs:
            if log.product and log.product.category_id:
                category_counter[log.product.category_id] += 1
        
        preferred_categories = [cat_id for cat_id, _ in category_counter.most_common(5)]
        browse_category_stats = {str(k): v for k, v in category_counter.items()}
        
        spending_level = "low"
        if avg_order_amount > 1000:
            spending_level = "high"
        elif avg_order_amount > 500:
            spending_level = "medium"
        
        region = self._get_region(user)
        
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if profile:
            profile.total_spent = float(total_spent)
            profile.order_count = order_count
            profile.avg_order_amount = avg_order_amount
            profile.preferred_categories = preferred_categories
            profile.browse_category_stats = browse_category_stats
            profile.spending_level = spending_level
            profile.region = region
            profile.last_updated = datetime.utcnow()
        else:
            from app.model.user import SpendingLevel
            profile = UserProfile(
                user_id=user_id,
                total_spent=float(total_spent),
                order_count=order_count,
                avg_order_amount=avg_order_amount,
                preferred_categories=preferred_categories,
                browse_category_stats=browse_category_stats,
                spending_level=SpendingLevel[spending_level.upper()],
                region=region,
                last_updated=datetime.utcnow()
            )
            self.db.add(profile)
        
        self.db.commit()
        return profile
    
    def _get_region(self, user):
        from app.model.log import LoginLog
        
        login_logs = self.db.query(LoginLog).filter(
            LoginLog.user_id == user.id
        ).order_by(LoginLog.created_at.desc()).limit(10).all()
        
        if not login_logs:
            return "未知"
        
        ip_prefixes = []
        for log in login_logs:
            if log.ip_address:
                parts = log.ip_address.split('.')
                if len(parts) >= 1:
                    ip_prefixes.append(parts[0])
        
        if not ip_prefixes:
            return "未知"
        
        most_common = Counter(ip_prefixes).most_common(1)[0][0]
        
        region_map = {
            "10": "内网",
            "127": "本机",
            "192": "局域网",
            "172": "局域网",
        }
        
        return region_map.get(most_common, "其他")
    
    def run(self):
        from app.model.user import User
        print("[Analysis] Analyzing user profiles...")
        
        users = self.db.query(User).filter(
            User.role_id == 1
        ).all()
        
        count = 0
        for user in users:
            if self.analyze_user(user.id):
                count += 1
        
        print(f"[Analysis] Analyzed {count} user profiles")
        return count
    
    def get_user_stats(self):
        from app.model.user import UserProfile
        from app.model.user import SpendingLevel
        from sqlalchemy import func
        
        total = self.db.query(UserProfile).count()
        
        spending_dist = {
            "low": self.db.query(UserProfile).filter(
                UserProfile.spending_level == SpendingLevel.LOW
            ).count(),
            "medium": self.db.query(UserProfile).filter(
                UserProfile.spending_level == SpendingLevel.MEDIUM
            ).count(),
            "high": self.db.query(UserProfile).filter(
                UserProfile.spending_level == SpendingLevel.HIGH
            ).count(),
        }
        
        avg_spent = self.db.query(func.avg(UserProfile.total_spent)).scalar() or 0
        avg_orders = self.db.query(func.avg(UserProfile.order_count)).scalar() or 0
        
        region_dist = {}
        profiles = self.db.query(UserProfile).all()
        for p in profiles:
            r = p.region or "未知"
            region_dist[r] = region_dist.get(r, 0) + 1
        
        return {
            "total": total,
            "spending_distribution": spending_dist,
            "avg_spent": float(avg_spent),
            "avg_orders": float(avg_orders),
            "region_distribution": region_dist
        }


class SalesAnalyzer:
    def __init__(self, db):
        self.db = db
    
    def analyze_daily_sales(self, date=None):
        from app.model.order import Order, OrderStatus
        from app.model.log import SalesStat
        from sqlalchemy import func
        
        if date is None:
            date = datetime.utcnow().date()
        
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())
        
        orders = self.db.query(Order).filter(
            Order.created_at >= start,
            Order.created_at <= end,
            Order.status == OrderStatus.CONFIRMED
        ).all()
        
        total_amount = sum(o.total_amount for o in orders)
        order_count = len(orders)
        user_count = len(set(o.user_id for o in orders))
        
        stat = self.db.query(SalesStat).filter(
            func.date(SalesStat.stat_date) == date
        ).first()
        
        if stat:
            stat.total_amount = total_amount
            stat.order_count = order_count
            stat.user_count = user_count
        else:
            stat = SalesStat(
                stat_date=datetime.combine(date, datetime.min.time()),
                total_amount=total_amount,
                order_count=order_count,
                user_count=user_count
            )
            self.db.add(stat)
        
        self.db.commit()
        return {"date": date, "amount": total_amount, "orders": order_count}
    
    def predict_trend(self, days=7):
        from app.model.log import SalesStat
        from sqlalchemy import func
        
        stats = self.db.query(SalesStat).order_by(
            SalesStat.stat_date.desc()
        ).limit(30).all()
        
        if len(stats) < 7:
            return {"trend": "insufficient_data", "prediction": None}
        
        amounts = [float(s.total_amount) for s in stats[:7]]
        avg = sum(amounts) / len(amounts)
        
        trend = "stable"
        if amounts[-1] > amounts[0] * 1.2:
            trend = "increasing"
        elif amounts[-1] < amounts[0] * 0.8:
            trend = "decreasing"
        
        return {
            "trend": trend,
            "current_avg": avg,
            "prediction": avg * 1.05 if trend == "increasing" else avg
        }
    
    def run(self, days=30):
        print(f"[Analysis] Analyzing sales for last {days} days...")
        
        for i in range(days):
            date = datetime.utcnow().date() - timedelta(days=i)
            self.analyze_daily_sales(date)
        
        print(f"[Analysis] Analyzed {days} days of sales")


class ProductRanker:
    def __init__(self, db):
        self.db = db
    
    def calculate_rank(self, period="daily", days=7):
        from app.model.product import Product, ProductRank
        from app.model.order import Order, OrderStatus
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        product_scores = defaultdict(float)
        
        orders = self.db.query(Order).filter(
            Order.created_at >= start_date,
            Order.status == OrderStatus.CONFIRMED
        ).all()
        
        for order in orders:
            for item in order.items:
                score = item.quantity * float(item.price)
                product_scores[item.product_id] += score
        
        sorted_products = sorted(
            product_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for rank, (product_id, score) in enumerate(sorted_products, 1):
            existing = self.db.query(ProductRank).filter(
                ProductRank.product_id == product_id,
                ProductRank.period == period
            ).first()
            
            if existing:
                existing.rank_score = score
                existing.rank_position = rank
                existing.last_analysis_at = datetime.utcnow()
            else:
                from app.model.product import ProductRankPeriod
                rank_obj = ProductRank(
                    product_id=product_id,
                    rank_score=score,
                    rank_position=rank,
                    period=ProductRankPeriod[period.upper()],
                    last_analysis_at=datetime.utcnow()
                )
                self.db.add(rank_obj)
        
        self.db.commit()
        print(f"[Analysis] Ranked {len(sorted_products)} products ({period})")
        return sorted_products
    
    def run(self):
        daily = self.calculate_rank("daily", days=1)
        weekly = self.calculate_rank("weekly", days=7)
        monthly = self.calculate_rank("monthly", days=30)
        
        return {
            "daily": daily[:10],
            "weekly": weekly[:10],
            "monthly": monthly[:10]
        }


class AnomalyDetector:
    def __init__(self, db):
        self.db = db
    
    def detect_anomalies(self):
        from app.model.log import AnomalyLog, AnomalySeverity
        
        anomalies = []
        
        large_orders = self._detect_large_orders()
        anomalies.extend(large_orders)
        
        failed_logins = self._detect_failed_logins()
        anomalies.extend(failed_logins)
        
        low_stock = self._detect_low_stock()
        anomalies.extend(low_stock)
        
        for anomaly in anomalies:
            existing = self.db.query(AnomalyLog).filter(
                AnomalyLog.anomaly_type == anomaly["type"],
                AnomalyLog.description == anomaly["description"],
                AnomalyLog.created_at > datetime.utcnow() - timedelta(hours=1)
            ).first()
            
            if not existing:
                log = AnomalyLog(
                    anomaly_type=anomaly["type"],
                    description=anomaly["description"],
                    severity=AnomalySeverity[anomaly["severity"].upper()],
                    details=anomaly.get("details")
                )
                self.db.add(log)
        
        self.db.commit()
        return len(anomalies)
    
    def _detect_large_orders(self):
        from app.model.order import Order, OrderStatus
        
        anomalies = []
        
        large_orders = self.db.query(Order).filter(
            Order.status == OrderStatus.CONFIRMED,
            Order.total_amount > 10000
        ).all()
        
        for order in large_orders:
            severity = "medium" if float(order.total_amount) < 50000 else "high"
            anomalies.append({
                "type": "large_order",
                "description": f"大额订单: ¥{order.total_amount}",
                "severity": severity,
                "details": {"order_id": order.id, "amount": float(order.total_amount)}
            })
        
        return anomalies
    
    def _detect_failed_logins(self):
        from app.model.log import LoginLog
        from sqlalchemy import func
        
        anomalies = []
        
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        failed = self.db.query(
            LoginLog.username,
            func.count(LoginLog.id).label("count")
        ).filter(
            LoginLog.success == False,
            LoginLog.created_at > one_hour_ago
        ).group_by(LoginLog.username).having(func.count(LoginLog.id) >= 5).all()
        
        for username, count in failed:
            severity = "medium" if count < 10 else "high"
            anomalies.append({
                "type": "login_failures",
                "description": f"用户 {username} 1小时内失败 {count} 次登录",
                "severity": severity,
                "details": {"username": username, "count": count}
            })
        
        return anomalies
    
    def _detect_low_stock(self):
        from app.model.product import Product
        
        anomalies = []
        
        low_stock = self.db.query(Product).filter(
            Product.is_active == True,
            Product.stock < 5
        ).all()
        
        for product in low_stock:
            anomalies.append({
                "type": "low_stock",
                "description": f"商品 {product.name} 库存不足 ({product.stock})",
                "severity": "low",
                "details": {"product_id": product.id, "stock": product.stock}
            })
        
        return anomalies
    
    def get_anomaly_stats(self):
        from app.model.log import AnomalyLog, AnomalySeverity
        from sqlalchemy import func
        
        total = self.db.query(AnomalyLog).count()
        unresolved = self.db.query(AnomalyLog).filter(
            AnomalyLog.is_resolved == False
        ).count()
        
        by_severity = {
            "high": self.db.query(AnomalyLog).filter(
                AnomalyLog.severity == AnomalySeverity.HIGH,
                AnomalyLog.is_resolved == False
            ).count(),
            "medium": self.db.query(AnomalyLog).filter(
                AnomalyLog.severity == AnomalySeverity.MEDIUM,
                AnomalyLog.is_resolved == False
            ).count(),
            "low": self.db.query(AnomalyLog).filter(
                AnomalyLog.severity == AnomalySeverity.LOW,
                AnomalyLog.is_resolved == False
            ).count(),
        }
        
        recent = self.db.query(AnomalyLog).filter(
            AnomalyLog.created_at > datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        return {
            "total": total,
            "unresolved": unresolved,
            "by_severity": by_severity,
            "last_24h": recent
        }
    
    def resolve_anomaly(self, anomaly_id):
        from app.model.log import AnomalyLog
        
        anomaly = self.db.query(AnomalyLog).filter(AnomalyLog.id == anomaly_id).first()
        if anomaly:
            anomaly.is_resolved = True
            anomaly.resolved_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def run(self):
        count = self.detect_anomalies()
        print(f"[AnomalyDetector] Detected {count} anomalies")


def main():
    from app.model.database import SessionLocal
    
    db = SessionLocal()
    
    try:
        print(f"[Analysis] Starting analysis at {datetime.now()}")
        
        profiler = UserProfiler(db)
        profiler.run()
        
        analyzer = SalesAnalyzer(db)
        analyzer.run(days=30)
        
        ranker = ProductRanker(db)
        ranker.run()
        
        anomaly = AnomalyDetector(db)
        anomaly.run()
        
        print(f"[Analysis] Completed at {datetime.now()}")
        
    except Exception as e:
        print(f"[Error] {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()