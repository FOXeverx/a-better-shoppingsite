import time
from fastapi import Request, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.config import get_config
from app.model.database import get_db
from app.model.log import SecurityThreat, IPBlock, ThreatType, ThreatSeverity, BlockType

config = get_config()


def get_db_session():
    from app.model.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_ip_blocked(db: Session, ip: str) -> bool:
    """检查IP是否被封禁"""
    blocked = db.query(IPBlock).filter(
        IPBlock.ip_address == ip
    ).filter(
        (IPBlock.expires_at == None) | (IPBlock.expires_at > datetime.utcnow())
    ).first()
    return blocked is not None


def block_ip(db: Session, ip: str, block_type: BlockType, reason: str, expires_minutes: int = 30):
    """封禁IP"""
    existing = db.query(IPBlock).filter(IPBlock.ip_address == ip).first()
    if existing:
        existing.block_type = block_type
        existing.reason = reason
        existing.expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes) if expires_minutes else None
    else:
        ip_block = IPBlock(
            ip_address=ip,
            block_type=block_type,
            reason=reason,
            expires_at=datetime.utcnow() + timedelta(minutes=expires_minutes) if expires_minutes else None
        )
        db.add(ip_block)
    db.commit()


def log_threat(db: Session, threat_type: ThreatType, ip: str, user_agent: str, details: dict, severity: ThreatSeverity = ThreatSeverity.MEDIUM):
    """记录安全威胁"""
    threat = SecurityThreat(
        threat_type=threat_type,
        ip_address=ip,
        user_agent=user_agent,
        details=details,
        severity=severity
    )
    db.add(threat)
    db.commit()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, ip_limit: int = None):
        super().__init__(app)
        self.ip_limit = ip_limit or config.security.ip_limit_per_minute
        self.ip_requests = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        from app.model.database import SessionLocal
        db = SessionLocal()
        try:
            client_ip = request.client.host if request.client else "unknown"
            current_time = time.time()
            user_agent = request.headers.get("user-agent", "")
            path = request.url.path
            
            # 检查是否被封禁
            if is_ip_blocked(db, client_ip):
                log_threat(
                    db, ThreatType.BLOCKED_IP, client_ip, user_agent,
                    {"path": path, "reason": "IP already blocked"}, ThreatSeverity.HIGH
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "IP blocked"}
                )
            
            # 清理60秒前的记录
            self.ip_requests[client_ip] = [
                t for t in self.ip_requests[client_ip]
                if current_time - t < 60
            ]
            
            # 检查是否超过限制
            if len(self.ip_requests[client_ip]) >= self.ip_limit:
                # 记录威胁
                log_threat(
                    db, ThreatType.RATE_LIMIT, client_ip, user_agent,
                    {"path": path, "request_count": len(self.ip_requests[client_ip])}, ThreatSeverity.MEDIUM
                )
                # 封禁IP
                block_ip(db, client_ip, BlockType.AUTO, "Rate limit exceeded", 30)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded, IP blocked for 30 minutes"}
                )
            
            self.ip_requests[client_ip].append(current_time)
            
            response = await call_next(request)
            return response
        finally:
            db.close()


class UserAgentMiddleware(BaseHTTPMiddleware):
    DISALLOWED_USER_AGENTS = [
        "python-requests",
        "curl",
        "wget",
        "scrapy"
    ]
    
    async def dispatch(self, request: Request, call_next):
        from app.model.database import SessionLocal
        db = SessionLocal()
        try:
            user_agent = request.headers.get("user-agent", "").lower()
            client_ip = request.client.host if request.client else "unknown"
            path = request.url.path
            
            for disallowed in self.DISALLOWED_USER_AGENTS:
                if disallowed in user_agent:
                    # 记录威胁
                    log_threat(
                        db, ThreatType.BLOCKED_UA, client_ip, user_agent,
                        {"path": path, "disallowed_ua": disallowed}, ThreatSeverity.HIGH
                    )
                    # 封禁IP
                    block_ip(db, client_ip, BlockType.AUTO, f"Blocked UA: {disallowed}", 30)
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Access denied, IP blocked for 30 minutes"}
                    )
            
            response = await call_next(request)
            return response
        finally:
            db.close()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # HSTS disabled for HTTP-only deployment
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response