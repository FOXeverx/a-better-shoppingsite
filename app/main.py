from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import load_config, get_config
from app.model.database import engine, Base
from fastapi.staticfiles import StaticFiles
from app.router import auth, product, cart, order, recommend, admin, log, user
from app.upload import router as upload_router
from app.middleware.security import (
    RateLimitMiddleware,
    UserAgentMiddleware,
    SecurityHeadersMiddleware
)

config = load_config()

app = FastAPI(
    title="Shopping Site Pro API",
    description="E-commerce Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(UserAgentMiddleware)
app.add_middleware(RateLimitMiddleware)


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    
    from app.model.user import Role
    from app.model.database import SessionLocal
    
    db = SessionLocal()
    try:
        existing_roles = db.query(Role).count()
        if existing_roles == 0:
            roles = ["customer", "sales", "admin"]
            for name in roles:
                role = Role(name=name)
                db.add(role)
            db.commit()
    finally:
        db.close()


@app.get("/")
async def root():
    return {
        "message": "Welcome to Shopping Site Pro API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


app.include_router(auth.router)
app.include_router(product.router)
app.include_router(cart.router)
app.include_router(order.router)
app.include_router(recommend.router)
app.include_router(admin.router)
app.include_router(log.router)
app.include_router(user.router)
app.include_router(upload_router, prefix="/api")

from app.config import get_config
app.mount("/uploads", StaticFiles(directory=str(Path(__file__).parent / "uploads")), name="uploads")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.app.host,
        port=config.app.port,
        reload=config.app.debug
    )