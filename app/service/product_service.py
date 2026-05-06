from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.model.product import Product, Category, ProductRank
from app.model.log import OperationLog


class ProductService:
    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
        return db.query(Product).filter(
            Product.id == product_id,
            Product.is_active == True
        ).first()
    
    @staticmethod
    def get_products(
        db: Session,
        category_id: int = None,
        search: str = None,
        min_price: Decimal = None,
        max_price: Decimal = None,
        sort: str = "created_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Product], int]:
        query = db.query(Product).filter(Product.is_active == True)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if search:
            query = query.filter(Product.name.contains(search))
        
        if min_price:
            query = query.filter(Product.price >= min_price)
        
        if max_price:
            query = query.filter(Product.price <= max_price)
        
        if sort == "price":
            order_col = Product.price
        elif sort == "name":
            order_col = Product.name
        else:
            order_col = Product.created_at
        
        if order == "desc":
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())
        
        total = query.count()
        products = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return products, total
    
    @staticmethod
    def create_product(
        db: Session,
        name: str,
        price: Decimal,
        stock: int,
        description: str = None,
        category_id: int = None,
        image_url: str = None,
        created_by: int = None
    ) -> Product:
        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category_id=category_id,
            image_url=image_url
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        
        if created_by:
            log = OperationLog(
                user_id=created_by,
                action="CREATE_PRODUCT",
                target_type="product",
                target_id=product.id,
                details=f'{{"name": "{name}", "price": {price}}}'
            )
            db.add(log)
            db.commit()
        
        return product
    
    @staticmethod
    def update_product(
        db: Session,
        product: Product,
        name: str = None,
        price: Decimal = None,
        stock: int = None,
        description: str = None,
        category_id: int = None,
        image_url: str = None,
        updated_by: int = None
    ) -> Product:
        if name:
            product.name = name
        if price is not None:
            product.price = price
        if stock is not None:
            product.stock = stock
        if description is not None:
            product.description = description
        if category_id is not None:
            product.category_id = category_id
        if image_url is not None:
            product.image_url = image_url
        
        db.commit()
        db.refresh(product)
        
        if updated_by:
            log = OperationLog(
                user_id=updated_by,
                action="UPDATE_PRODUCT",
                target_type="product",
                target_id=product.id
            )
            db.add(log)
            db.commit()
        
        return product
    
    @staticmethod
    def delete_product(
        db: Session,
        product: Product,
        deleted_by: int = None
    ) -> bool:
        product.is_active = False
        db.commit()
        
        if deleted_by:
            log = OperationLog(
                user_id=deleted_by,
                action="DELETE_PRODUCT",
                target_type="product",
                target_id=product.id
            )
            db.add(log)
            db.commit()
        
        return True
    
    @staticmethod
    def adjust_stock(
        db: Session,
        product: Product,
        quantity: int,
        updated_by: int = None
    ) -> Product:
        product.stock += quantity
        if product.stock < 0:
            product.stock = 0
        db.commit()
        db.refresh(product)
        
        if updated_by:
            log = OperationLog(
                user_id=updated_by,
                action="ADJUST_STOCK",
                target_type="product",
                target_id=product.id,
                details=f'{{"quantity": {quantity}}}'
            )
            db.add(log)
            db.commit()
        
        return product


class CategoryService:
    @staticmethod
    def get_categories(db: Session) -> List[Category]:
        return db.query(Category).filter(Category.parent_id == None).all()
    
    @staticmethod
    def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
        return db.query(Category).filter(Category.id == category_id).first()
    
    @staticmethod
    def create_category(
        db: Session,
        name: str,
        parent_id: int = None
    ) -> Category:
        category = Category(name=name, parent_id=parent_id)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def get_category_tree(db: Session) -> List[dict]:
        categories = db.query(Category).all()
        return CategoryService._build_tree(categories)
    
    @staticmethod
    def _build_tree(categories: List[Category]) -> List[dict]:
        category_map = {c.id: {"id": c.id, "name": c.name, "parent_id": c.parent_id, "children": []} for c in categories}
        tree = []
        for c in categories:
            if c.parent_id:
                if c.parent_id in category_map:
                    category_map[c.parent_id]["children"].append(category_map[c.id])
            else:
                tree.append(category_map[c.id])
        return tree