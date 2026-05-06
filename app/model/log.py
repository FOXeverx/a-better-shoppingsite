from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text, JSON, DECIMAL, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.model.database import Base
import enum


class AnomalySeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ThreatSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, enum.Enum):
    RATE_LIMIT = "rate_limit"          # 触发限流
    BLOCKED_IP = "blocked_ip"           # IP被封禁
    BLOCKED_UA = "blocked_ua"           # UA被拦截
    BRUTE_FORCE = "brute_force"         # 暴力破解
    SUSPICIOUS_ACCESS = "suspicious_access"  # 可疑访问


class BlockType(str, enum.Enum):
    MANUAL = "manual"   # 手动封禁
    AUTO = "auto"        # 自动封禁


class LoginLog(Base):
    __tablename__ = "login_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    username = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=True)
    success = Column(Boolean, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="login_logs")


class BrowseLog(Base):
    __tablename__ = "browse_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False)
    stay_time = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="browse_logs")
    product = relationship("Product", back_populates="browse_logs")


class OperationLog(Base):
    __tablename__ = "operation_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="operation_logs")


class SalesStat(Base):
    __tablename__ = "sales_stat"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(DateTime, nullable=False, unique=True)
    total_amount = Column(Numeric(12, 2), default=0)
    order_count = Column(Integer, default=0)
    user_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AnomalyLog(Base):
    __tablename__ = "anomaly_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    anomaly_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Enum(AnomalySeverity), default=AnomalySeverity.MEDIUM)
    details = Column(JSON, nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)


class SecurityThreat(Base):
    __tablename__ = "security_threat"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    threat_type = Column(Enum(ThreatType), nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True)
    severity = Column(Enum(ThreatSeverity), default=ThreatSeverity.MEDIUM)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)


class IPBlock(Base):
    __tablename__ = "ip_block"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(45), nullable=False, unique=True)
    block_type = Column(Enum(BlockType), nullable=False)
    reason = Column(String(200), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    created_by = relationship("User")


class VerificationCode(Base):
    __tablename__ = "verification_code"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), nullable=False)
    code = Column(String(6), nullable=False)
    purpose = Column(String(20), nullable=False, default="register")
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())