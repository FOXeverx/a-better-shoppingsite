from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.model.database import Base
import enum


class ProductRankPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Category(Base):
    __tablename__ = "category"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey("category.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "product"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=True)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    category = relationship("Category", back_populates="products")
    carts = relationship("Cart", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    browse_logs = relationship("BrowseLog", back_populates="product")
    product_ranks = relationship("ProductRank", back_populates="product", cascade="all, delete-orphan")
    recommend_sources = relationship(
        "RecommendItem",
        foreign_keys="RecommendItem.product_id",
        back_populates="source_product"
    )
    recommend_targets = relationship(
        "RecommendItem",
        foreign_keys="RecommendItem.recommend_product_id",
        back_populates="target_product"
    )
    comments = relationship("Comment", back_populates="product", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comment"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    product = relationship("Product", back_populates="comments")
    user = relationship("User", back_populates="comments")


class ProductRank(Base):
    __tablename__ = "product_rank"
    __table_args__ = (
        UniqueConstraint("product_id", "period", name="uk_product_period"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    rank_score = Column(Numeric(10, 2), default=0)
    rank_position = Column(Integer, nullable=True)
    period = Column(Enum(ProductRankPeriod), default=ProductRankPeriod.DAILY)
    last_analysis_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    product = relationship("Product", back_populates="product_ranks")


class RecommendItem(Base):
    __tablename__ = "recommend_item"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    recommend_product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    score = Column(Numeric(5, 4), default=0)
    algorithm = Column(String(50), default="cooccurrence")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    source_product = relationship(
        "Product",
        foreign_keys=[product_id],
        back_populates="recommend_sources"
    )
    target_product = relationship(
        "Product",
        foreign_keys=[recommend_product_id],
        back_populates="recommend_targets"
    )