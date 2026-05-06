"""
Recommendation System Script
- Co-occurrence based recommendation
- Item-based collaborative filtering
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict
from decimal import Decimal
from datetime import datetime
import yaml


def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class CooccurrenceRecommender:
    def __init__(self, db):
        self.db = db
    
    def build_cooccurrence_matrix(self):
        from app.model.order import Order, OrderItem, OrderStatus
        from sqlalchemy import func
        
        orders = self.db.query(Order).filter(
            Order.status == OrderStatus.CONFIRMED
        ).all()
        
        cooccurrence = defaultdict(lambda: defaultdict(int))
        
        for order in orders:
            product_ids = [item.product_id for item in order.items]
            
            for i, p1 in enumerate(product_ids):
                for p2 in product_ids:
                    if p1 != p2:
                        cooccurrence[p1][p2] += 1
        
        return cooccurrence
    
    def calculate_similarity(self, cooccurrence, product_id):
        if product_id not in cooccurrence:
            return {}
        
        target_products = cooccurrence[product_id]
        total = sum(target_products.values())
        
        if total == 0:
            return {}
        
        similarities = {}
        for product_id, count in target_products.items():
            similarities[product_id] = count / total
        
        return similarities
    
    def run(self):
        from app.model.product import Product, RecommendItem
        from app.model.order import Order, OrderItem
        
        print("[Recommender] Building co-occurrence matrix...")
        
        cooccurrence = self.build_cooccurrence_matrix()
        
        products = self.db.query(Product).filter(
            Product.is_active == True
        ).all()
        
        print(f"[Recommender] Processing {len(products)} products...")
        
        self.db.query(RecommendItem).delete()
        self.db.commit()
        
        count = 0
        for product in products:
            similarities = self.calculate_similarity(cooccurrence, product.id)
            
            sorted_sims = sorted(
                similarities.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            for related_product_id, score in sorted_sims:
                recommend_item = RecommendItem(
                    product_id=product.id,
                    recommend_product_id=related_product_id,
                    score=Decimal(str(score)),
                    algorithm="cooccurrence"
                )
                self.db.add(recommend_item)
                count += 1
        
        self.db.commit()
        print(f"[Recommender] Created {count} recommendations")
        
        return count


class CollaborativeFilter:
    def __init__(self, db):
        self.db = db
    
    def calculate_item_similarity(self, product_id, user_products, product_users):
        if product_id not in product_users:
            return {}
        
        target_users = product_users[product_id]
        
        target_products = set()
        for uid in target_users:
            target_products.update(user_products[uid])
        
        similarities = defaultdict(int)
        for user_id, products in user_products.items():
            if user_id in target_users:
                continue
            common = len(products & target_products)
            if common > 0:
                similarities[user_id] = common
        
        return similarities
    
    def run(self):
        from app.model.product import Product, RecommendItem
        from app.model.order import Order, OrderItem, OrderStatus
        from collections import Counter
        
        print("[Collaborative] Building user-product mappings...")
        
        orders = self.db.query(Order).filter(
            Order.status == OrderStatus.CONFIRMED
        ).all()
        
        user_products = defaultdict(set)
        product_users = defaultdict(set)
        for order in orders:
            for item in order.items:
                user_products[order.user_id].add(item.product_id)
                product_users[item.product_id].add(order.user_id)
        
        print("[Collaborative] Calculating item similarities...")
        
        products = self.db.query(Product).filter(
            Product.is_active == True
        ).all()
        
        for product in products:
            similar_users = self.calculate_item_similarity(
                product.id, user_products, product_users
            )
            
            if not similar_users:
                continue
            
            product_scores = Counter()
            
            for user_id, weight in similar_users.items():
                user_orders = self.db.query(Order).filter(
                    Order.user_id == user_id,
                    Order.status == OrderStatus.CONFIRMED
                ).all()
                
                for order in user_orders:
                    for item in order.items:
                        if item.product_id != product.id:
                            product_scores[item.product_id] += weight
            
            for related_product_id, score in product_scores.most_common(5):
                existing = self.db.query(RecommendItem).filter(
                    RecommendItem.product_id == product.id,
                    RecommendItem.recommend_product_id == related_product_id
                ).first()
                
                if existing:
                    existing.score = existing.score + Decimal(str(score / 100))
                    existing.algorithm = "cooccurrence+collaborative"
                else:
                    recommend_item = RecommendItem(
                        product_id=product.id,
                        recommend_product_id=related_product_id,
                        score=Decimal(str(score / 100)),
                        algorithm="collaborative"
                    )
                    self.db.add(recommend_item)
        
        self.db.commit()
        print("[Collaborative] Collaborative filtering completed")
        


def main():
    from app.model.database import SessionLocal
    config = load_config()
    
    db = SessionLocal()
    
    try:
        cooccurrence = CooccurrenceRecommender(db)
        cooccurrence.run()
        
        collaborative = CollaborativeFilter(db)
        collaborative.run()
        
        print(f"[Recommender] Completed at {datetime.now()}")
        
    except Exception as e:
        print(f"[Error] {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()