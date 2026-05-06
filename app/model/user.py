from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.model.database import Base
import enum


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    SALES = "sales"
    ADMIN = "admin"


class SpendingLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Role(Base):
    __tablename__ = "role"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True, comment="Role name")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, comment="Username")
    password_hash = Column(String(255), nullable=False, comment="Bcrypt hashed password")
    email = Column(String(100), nullable=False, unique=True, comment="User email")
    role_id = Column(Integer, ForeignKey("role.id"), nullable=False, default=1)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    login_attempts = Column(Integer, default=0)
    blocked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    role = relationship("Role", back_populates="users")
    carts = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    login_logs = relationship("LoginLog", back_populates="user")
    browse_logs = relationship("BrowseLog", back_populates="user", cascade="all, delete-orphan")
    operation_logs = relationship("OperationLog", back_populates="user", cascade="all, delete-orphan")
    profiles = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user")
    
    @property
    def role_name(self) -> str:
        return self.role.name if self.role else "customer"


class UserProfile(Base):
    __tablename__ = "user_profile"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, unique=True)
    region = Column(String(50), nullable=True)
    total_spent = Column(Numeric(12, 2), default=0)
    order_count = Column(Integer, default=0)
    avg_order_amount = Column(Numeric(12, 2), default=0)
    preferred_categories = Column(JSON, nullable=True)
    browse_category_stats = Column(JSON, nullable=True)
    spending_level = Column(Enum(SpendingLevel), default=SpendingLevel.LOW)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="profiles")