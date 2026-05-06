from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session
from app.model.database import get_db
from app.dependencies import get_current_user, require_role
from app.model.user import User
from app.model.product import Product, Category, Comment
from app.service.product_service import ProductService, CategoryService

router = APIRouter(prefix="/api/product", tags=["product"])


class ProductResponse(BaseModel):
    success: bool = True
    data: Optional[dict] = None
    message: str = ""


class ProductListResponse(BaseModel):
    success: bool = True
    data: List[dict] = []
    pagination: Optional[dict] = None


class ProductCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    stock: int
    category_id: Optional[int] = None
    image_url: Optional[str] = None


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None


@router.get("", response_model=ProductListResponse)
async def get_products(
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[Decimal] = Query(None),
    max_price: Optional[Decimal] = Query(None),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
    page: int = Query(1),
    page_size: int = Query(20),
    db: Session = Depends(get_db)
):
    products, total = ProductService.get_products(
        db=db,
        category_id=category_id,
        search=search,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size
    )
    
    data = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": float(p.price),
            "stock": p.stock,
            "category_id": p.category_id,
            "image_url": p.image_url,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in products
    ]
    
    total_pages = (total + page_size - 1) // page_size
    
    return ProductListResponse(
        data=data,
        pagination={
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }
    )


@router.get("/category/list")
async def get_categories(db: Session = Depends(get_db)):
    categories = CategoryService.get_category_tree(db)
    return {"success": True, "data": categories}


@router.get("/category")
async def get_category_list(
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    categories = db.query(Category).order_by(Category.id).all()
    return {
        "success": True,
        "data": [
            {
                "id": c.id,
                "name": c.name,
                "parent_id": c.parent_id
            }
            for c in categories
        ]
    }


class CategoryRequest(BaseModel):
    name: str
    parent_id: Optional[int] = None


@router.post("/category")
async def create_category(
    req: CategoryRequest,
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    category = CategoryService.create_category(db, req.name, req.parent_id)
    return {
        "success": True,
        "data": {
            "id": category.id,
            "name": category.name,
            "parent_id": category.parent_id
        },
        "message": "Category created successfully"
    }


@router.put("/category/{category_id}")
async def update_category(
    category_id: int,
    req: CategoryRequest,
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    category = CategoryService.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    category.name = req.name
    if req.parent_id is not None:
        category.parent_id = req.parent_id
    db.commit()
    db.refresh(category)
    
    return {
        "success": True,
        "data": {
            "id": category.id,
            "name": category.name,
            "parent_id": category.parent_id
        },
        "message": "Category updated successfully"
    }


@router.delete("/category/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    category = CategoryService.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    from app.model.product import Product
    db.query(Product).filter(Product.category_id == category_id).update(
        {"category_id": None}
    )
    
    children = db.query(Category).filter(Category.parent_id == category_id).all()
    for child in children:
        child.parent_id = None
    
    db.delete(category)
    db.commit()
    
    return {"success": True, "message": "Category deleted successfully"}


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = ProductService.get_product_by_id(db, product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    category = None
    if product.category:
        category = {
            "id": product.category.id,
            "name": product.category.name
        }
    
    return ProductResponse(
        data={
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "stock": product.stock,
            "category": category,
            "image_url": product.image_url,
            "is_active": product.is_active,
            "created_at": product.created_at.isoformat() if product.created_at else None,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None
        }
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    req: ProductCreateRequest,
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    product = ProductService.create_product(
        db=db,
        name=req.name,
        description=req.description,
        price=req.price,
        stock=req.stock,
        category_id=req.category_id,
        image_url=req.image_url,
        created_by=current_user.id
    )
    
    return ProductResponse(
        data={
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "stock": product.stock
        },
        message="Product created successfully"
    )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    req: ProductUpdateRequest,
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    print(f"Update request - product_id: {product_id}, image_url: {req.image_url}, name: {req.name}")
    product = ProductService.get_product_by_id(db, product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product = ProductService.update_product(
        db=db,
        product=product,
        name=req.name,
        price=req.price,
        stock=req.stock,
        description=req.description,
        category_id=req.category_id,
        image_url=req.image_url,
        updated_by=current_user.id
    )
    
    return ProductResponse(
        data={
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "stock": product.stock
        },
        message="Product updated successfully"
    )


@router.delete("/{product_id}", response_model=ProductResponse)
async def delete_product(
    product_id: int,
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    product = ProductService.get_product_by_id(db, product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    ProductService.delete_product(
        db=db,
        product=product,
        deleted_by=current_user.id
    )
    
    return ProductResponse(message="Product deleted successfully")


@router.get("/{product_id}/comments")
async def get_comments(
    product_id: int,
    db: Session = Depends(get_db)
):
    comments = db.query(Comment).filter(Comment.product_id == product_id).order_by(Comment.created_at.desc()).all()
    return {
        "success": True,
        "data": [
            {
                "id": c.id,
                "product_id": c.product_id,
                "user_id": c.user_id,
                "username": c.user.username,
                "content": c.content,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in comments
        ]
    }


class CommentRequest(BaseModel):
    content: str


@router.post("/{product_id}/comments")
async def add_comment(
    product_id: int,
    req: CommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = ProductService.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    comment = Comment(product_id=product_id, user_id=current_user.id, content=req.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return {
        "success": True,
        "data": {
            "id": comment.id,
            "product_id": comment.product_id,
            "user_id": comment.user_id,
            "username": current_user.username,
            "content": comment.content,
            "created_at": comment.created_at.isoformat() if comment.created_at else None
        },
        "message": "Comment added successfully"
    }


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(require_role("sales", "admin")),
    db: Session = Depends(get_db)
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    db.delete(comment)
    db.commit()
    
    return {"success": True, "message": "Comment deleted successfully"}