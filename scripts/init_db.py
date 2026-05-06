"""
Database initialization script
Run this script to initialize the database
"""

import sys
import os
import mysql.connector
import yaml


def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_database_if_not_exists(config):
    """创建数据库（如果不存在）"""
    conn = mysql.connector.connect(
        host=config["database"]["host"],
        port=config["database"]["port"],
        user=config["database"]["username"],
        passwd=config["database"]["password"]
    )
    cursor = conn.cursor()
    db_name = config["database"]["name"]
    
    # 检查数据库是否存在
    cursor.execute("SHOW DATABASES LIKE %s", (db_name,))
    result = cursor.fetchone()
    
    if not result:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {db_name} "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        print(f"Database '{db_name}' created")
    else:
        print(f"Database '{db_name}' already exists")
    
    conn.close()


def init_database_tables():
    """创建表"""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app.model.database import engine, Base
    from app.model.user import User, Role, UserProfile
    from app.model.product import Product, Category, ProductRank, RecommendItem
    from app.model.cart import Cart
    from app.model.order import Order, OrderItem
    from app.model.log import (
        LoginLog, BrowseLog, OperationLog, 
        SalesStat, AnomalyLog
    )
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # 插入默认角色
    from app.model.database import SessionLocal
    from app.service.auth_service import AuthService
    
    db = SessionLocal()
    try:
        existing_roles = db.query(Role).count()
        if existing_roles == 0:
            roles = ["customer", "sales", "admin"]
            for name in roles:
                role = Role(name=name)
                db.add(role)
            db.commit()
            print("Default roles created")
        
        # 创建默认管理员
        admin_exists = db.query(User).filter(User.username == "123456").first()
        if not admin_exists:
            admin_role = db.query(Role).filter(Role.name == "admin").first()
            if admin_role:
                admin_user = User(
                    username="123456",
                    email="3541692950@qq.com",
                    password_hash=AuthService.hash_password("123456"),
                    role=admin_role,
                    is_active=True
                )
                db.add(admin_user)
                db.commit()
                print("Default admin user created: username=123456, password=123456")
        
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    config = load_config()
    
    try:
        create_database_if_not_exists(config)
    except Exception as e:
        print(f"Error creating database: {e}")
        print("Please create database manually:")
        print("  CREATE DATABASE shopping_site CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    
    init_database_tables()
    print("Done!")