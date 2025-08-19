from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime
from enum import Enum
import models
from models import Base
from database import engine, get_db, check_db_connection
from pydantic import BaseModel, EmailStr, Field, validator
from security import get_password_hash, verify_password

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Product & User Management API with Categories",
    description="API for managing users, categories, and products with validation and database migrations",
    version="2.0.0"
)

# Check database connection on startup
@app.on_event("startup")
async def startup_event():
    print("\nChecking database connection...")
    if not check_db_connection():
        print("Application will continue running, but database operations may fail.")
    print("\nStarting FastAPI application...")

# Root endpoint with welcome message
@app.get("/")
async def root():
    return {
        "message": "Welcome to Product & User Management API with Categories", 
        "docs": "Visit /docs for API documentation",
        "version": "2.0.0",
        "endpoints": {
            "users": "/users/",
            "categories": "/categories/",
            "products": "/products/",
            "orders": "/orders/"
        }
    }

# Enhanced Pydantic models for User with validation
class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Full name (1-50 characters)")
    email: EmailStr = Field(..., description="Valid and unique email address")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100, description="Password minimum 8 characters")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        if any(char.isdigit() for char in v):
            raise ValueError('Name cannot contain numbers')
        return v.strip()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least 1 digit')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least 1 uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least 1 lowercase letter')
        return v

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Full name")
    email: Optional[EmailStr] = Field(None, description="Valid email address")
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="New password")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Name cannot be empty')
            if any(char.isdigit() for char in v):
                raise ValueError('Name cannot contain numbers')
            return v.strip()
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters')
            if not any(c.isdigit() for c in v):
                raise ValueError('Password must contain at least 1 digit')
            if not any(c.isupper() for c in v):
                raise ValueError('Password must contain at least 1 uppercase letter')
            if not any(c.islower() for c in v):
                raise ValueError('Password must contain at least 1 lowercase letter')
        return v

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Enhanced Pydantic models for Category with validation
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name (1-100 characters)")
    description: Optional[str] = Field(None, max_length=255, description="Category description (optional)")

class CategoryCreate(CategoryBase):
    user_id: int = Field(..., gt=0, description="Category owner user ID")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None and v.strip():
            return v.strip()
        return v

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=255, description="Category description")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Category name cannot be empty')
            return v.strip()
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None and v.strip():
            return v.strip()
        return v

class Category(CategoryBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Enhanced Pydantic models for Product with validation
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Product name (1-100 characters)")
    stock: int = Field(..., ge=0, description="Product stock (must be >= 0)")
    price: float = Field(..., gt=0, description="Product price (must be > 0)")

class ProductCreate(ProductBase):
    category_id: int = Field(..., gt=0, description="Product category ID")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Product name cannot be empty')
        return v.strip()
    
    @validator('stock')
    def validate_stock(cls, v):
        if v < 0:
            raise ValueError('Stock cannot be negative')
        if v > 999999:
            raise ValueError('Stock maximum is 999999')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        if v > 999999999:
            raise ValueError('Price maximum is 999999999')
        return round(v, 2)

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Product name")
    stock: Optional[int] = Field(None, ge=0, description="Product stock")
    price: Optional[float] = Field(None, gt=0, description="Product price")
    category_id: Optional[int] = Field(None, gt=0, description="Product category ID")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Product name cannot be empty')
            return v.strip()
        return v
    
    @validator('stock')
    def validate_stock(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Stock cannot be negative')
            if v > 999999:
                raise ValueError('Stock maximum is 999999')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('Price must be greater than 0')
            if v > 999999999:
                raise ValueError('Price maximum is 999999999')
            return round(v, 2)
        return v

class Product(ProductBase):
    id: int
    category_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# USER API ENDPOINTS
@app.post("/user/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user with complete data validation"""
    try:
        # Check if email already exists
        existing_user = db.query(models.User).filter(models.User.email == user.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password before saving
        hashed_password = get_password_hash(user.password)
        
        # Create new user
        db_user = models.User(
            name=user.name,
            email=user.email,
            password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

@app.get("/users/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users with pagination"""
    if skip < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skip must be >= 0")
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Limit must be between 1-1000")
    
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@app.get("/user/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID must be > 0")
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@app.put("/user/{user_id}", response_model=User)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """Update user information"""
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID must be > 0")
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    try:
        # Update only provided fields
        if user.name is not None:
            db_user.name = user.name
        if user.email is not None:
            # Check if email already exists
            existing_user = db.query(models.User).filter(
                models.User.email == user.email,
                models.User.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already used by another user"
                )
            db_user.email = user.email
        if user.password is not None:
            hashed_password = get_password_hash(user.password)
            db_user.password = hashed_password
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already used by another user"
        )

@app.delete("/user/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete user"""
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID must be > 0")
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return {"message": f"User with ID {user_id} successfully deleted"}

@app.post("/user/verify-password/{user_id}")
def verify_user_password(user_id: int, password: str, db: Session = Depends(get_db)):
    """Verify user password"""
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID must be > 0")
    if not password or len(password.strip()) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password cannot be empty")
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if verify_password(password, db_user.password):
        return {"message": "Password is correct"}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password is incorrect") 

# CATEGORY API ENDPOINTS
@app.post("/category/", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category with complete data validation"""
    # Check if user_id is valid
    user_exists = db.query(models.User).filter(models.User.id == category.user_id).first()
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID not found"
        )
    
    db_category = models.Category(
        name=category.name,
        description=category.description,
        user_id=category.user_id
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/categories/", response_model=List[Category])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all categories with pagination"""
    if skip < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skip must be >= 0")
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Limit must be between 1-1000")
    
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    return categories

@app.get("/categories/user/{user_id}", response_model=List[Category])
def read_categories_by_user(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get categories by user ID"""
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID must be > 0")
    if skip < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skip must be >= 0")
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Limit must be between 1-1000")
    
    categories = db.query(models.Category).filter(models.Category.user_id == user_id).offset(skip).limit(limit).all()
    return categories

@app.get("/category/{category_id}", response_model=Category)
def read_category(category_id: int, db: Session = Depends(get_db)):
    """Get category by ID"""
    if category_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category ID must be > 0")
    
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return db_category

@app.put("/category/{category_id}", response_model=Category)
def update_category(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db)):
    """Update category information"""
    if category_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category ID must be > 0")
    
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # Update only provided fields
    if category.name is not None:
        db_category.name = category.name
    if category.description is not None:
        db_category.description = category.description
    
    db.commit()
    db.refresh(db_category)
    return db_category

@app.delete("/category/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete category"""
    if category_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category ID must be > 0")
    
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # Check if there are products using this category
    products_count = db.query(models.Product).filter(models.Product.category_id == category_id).count()
    if products_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category. There are {products_count} products using this category."
        )
    
    db.delete(db_category)
    db.commit()
    return {"message": f"Category with ID {category_id} successfully deleted"}

# PRODUCT API ENDPOINTS
@app.post("/product/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product with complete data validation"""
    # Check if category_id is valid
    category_exists = db.query(models.Category).filter(models.Category.id == product.category_id).first()
    if not category_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category ID not found"
        )
    
    db_product = models.Product(
        name=product.name,
        stock=product.stock,
        price=product.price,
        category_id=product.category_id
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=List[Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all products with pagination"""
    if skip < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skip must be >= 0")
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Limit must be between 1-1000")
    
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/category/{category_id}", response_model=List[Product])
def read_products_by_category(category_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get products by category"""
    if category_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category ID must be > 0")
    if skip < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skip must be >= 0")
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Limit must be between 1-1000")
    
    products = db.query(models.Product).filter(models.Product.category_id == category_id).offset(skip).limit(limit).all()
    return products

@app.get("/product/{product_id}", response_model=Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    """Get product by ID"""
    if product_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product ID must be > 0")
    
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return db_product

@app.put("/product/{product_id}", response_model=Product)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    """Update product information"""
    if product_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product ID must be > 0")
    
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # If category_id is updated, check its validity
    if product.category_id is not None:
        category_exists = db.query(models.Category).filter(models.Category.id == product.category_id).first()
        if not category_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category ID not found"
            )
    
    # Update only provided fields
    if product.name is not None:
        db_product.name = product.name
    if product.stock is not None:
        db_product.stock = product.stock
    if product.price is not None:
        db_product.price = product.price
    if product.category_id is not None:
        db_product.category_id = product.category_id
    
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/product/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete product"""
    if product_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product ID must be > 0")
    
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return {"message": f"Product with ID {product_id} successfully deleted"}

# Order Status Enum
class OrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Order Pydantic Models
class OrderItemBase(BaseModel):
    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity of product")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        if v > 999:
            raise ValueError('Quantity maximum is 999')
        return v

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemUpdate(BaseModel):
    product_id: Optional[int] = Field(None, gt=0, description="Product ID")
    quantity: Optional[int] = Field(None, gt=0, description="Quantity of product")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('Quantity must be greater than 0')
            if v > 999:
                raise ValueError('Quantity maximum is 999')
        return v

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    price: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    user_id: int = Field(..., gt=0, description="User ID who placed the order")

class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_items=1, description="List of items in the order")

class OrderUpdate(BaseModel):
    status: OrderStatus = Field(..., description="Order status (pending, completed, cancelled)")

class OrderWithUser(BaseModel):
    id: int
    user_id: int
    user_name: str
    total_amount: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    items: List[OrderItem]

    class Config:
        from_attributes = True

class Order(OrderBase):
    id: int
    total_amount: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    items: List[OrderItem]

    class Config:
        from_attributes = True

# ORDER API ENDPOINTS
@app.post("/order/", response_model=OrderWithUser, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """Create a new order with items"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == order.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Validate products and calculate total amount
    total_amount = 0
    order_items = []
    
    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with ID {item.product_id} not found"
            )
        
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.name}"
            )
        
        # Calculate item total and update product stock
        item_total = product.price * item.quantity
        total_amount += item_total
        
        # Create OrderItem
        order_items.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": product.price
        })
        
        # Update product stock
        product.stock -= item.quantity
    
    try:
        # Create order
        db_order = models.Order(
            user_id=order.user_id,
            total_amount=total_amount,
            status=OrderStatus.PENDING.value
        )
        db.add(db_order)
        db.flush()  # Get order ID without committing
        
        # Create order items
        for item_data in order_items:
            db_order_item = models.OrderItem(
                order_id=db_order.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                price=item_data["price"]
            )
            db.add(db_order_item)
        
        db.commit()
        db.refresh(db_order)
        
        # Convert to OrderWithUser format
        result = {
            "id": db_order.id,
            "user_id": db_order.user_id,
            "user_name": user.name,
            "total_amount": db_order.total_amount,
            "status": db_order.status,
            "created_at": db_order.created_at,
            "updated_at": db_order.updated_at,
            "items": db_order.items
        }
        
        return result
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )

@app.get("/orders/", response_model=List[OrderWithUser])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all orders with pagination and user information"""
    if skip < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skip must be >= 0")
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Limit must be between 1-1000")
    
    # Use left join to get orders with user information
    orders_with_users = db.query(
        models.Order,
        models.User.name.label('user_name')
    ).outerjoin(
        models.User, models.Order.user_id == models.User.id
    ).offset(skip).limit(limit).all()
    
    # Convert to OrderWithUser format
    result = []
    for order, user_name in orders_with_users:
        order_dict = {
            "id": order.id,
            "user_id": order.user_id,
            "user_name": user_name or "Unknown User",
            "total_amount": order.total_amount,
            "status": order.status,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": order.items
        }
        result.append(order_dict)
    
    return result

@app.get("/orders/user/{user_id}", response_model=List[OrderWithUser])
def read_user_orders(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get orders by user ID with user information"""
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID must be > 0")
    
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Use left join to get orders with user information
    orders_with_users = db.query(
        models.Order,
        models.User.name.label('user_name')
    ).outerjoin(
        models.User, models.Order.user_id == models.User.id
    ).filter(models.Order.user_id == user_id).offset(skip).limit(limit).all()
    
    # Convert to OrderWithUser format
    result = []
    for order, user_name in orders_with_users:
        order_dict = {
            "id": order.id,
            "user_id": order.user_id,
            "user_name": user_name or "Unknown User",
            "total_amount": order.total_amount,
            "status": order.status,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": order.items
        }
        result.append(order_dict)
    
    return result

@app.get("/order/{order_id}", response_model=OrderWithUser)
def read_order(order_id: int, db: Session = Depends(get_db)):
    """Get order by ID with user information"""
    if order_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order ID must be > 0")
    
    # Use left join to get order with user information
    order_with_user = db.query(
        models.Order,
        models.User.name.label('user_name')
    ).outerjoin(
        models.User, models.Order.user_id == models.User.id
    ).filter(models.Order.id == order_id).first()
    
    if not order_with_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    order, user_name = order_with_user
    
    # Convert to OrderWithUser format
    result = {
        "id": order.id,
        "user_id": order.user_id,
        "user_name": user_name or "Unknown User",
        "total_amount": order.total_amount,
        "status": order.status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": order.items
    }
    
    return result

@app.put("/order/{order_id}", response_model=OrderWithUser)
def update_order_status(order_id: int, order_update: OrderUpdate, db: Session = Depends(get_db)):
    """Update order status"""
    if order_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order ID must be > 0")
    
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # If cancelling order, restore product stock
    if order_update.status == OrderStatus.CANCELLED and order.status != OrderStatus.CANCELLED:
        for item in order.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product:
                product.stock += item.quantity
    
    order.status = order_update.status.value
    db.commit()
    db.refresh(order)
    
    # Get user information for response
    user = db.query(models.User).filter(models.User.id == order.user_id).first()
    user_name = user.name if user else "Unknown User"
    
    # Convert to OrderWithUser format
    result = {
        "id": order.id,
        "user_id": order.user_id,
        "user_name": user_name,
        "total_amount": order.total_amount,
        "status": order.status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": order.items
    }
    
    return result

@app.delete("/order/{order_id}", status_code=status.HTTP_200_OK)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    """Delete order"""
    if order_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order ID must be > 0")
    
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # If order is not cancelled, restore product stock
    if order.status != OrderStatus.CANCELLED:
        for item in order.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product:
                product.stock += item.quantity
    
    db.delete(order)
    db.commit()
    return {"message": f"Order with ID {order_id} successfully deleted"}

# ORDER ITEM API ENDPOINTS
@app.get("/order-item/{item_id}", response_model=OrderItem)
def read_order_item(item_id: int, db: Session = Depends(get_db)):
    """Get order item by ID"""
    if item_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item ID must be > 0")
    
    order_item = db.query(models.OrderItem).filter(models.OrderItem.id == item_id).first()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")
    return order_item

@app.put("/order-item/{item_id}", response_model=OrderItem)
def update_order_item(item_id: int, item_update: OrderItemUpdate, db: Session = Depends(get_db)):
    """Update order item"""
    if item_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item ID must be > 0")
    
    order_item = db.query(models.OrderItem).filter(models.OrderItem.id == item_id).first()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")
    
    # Get the order to check if it can be modified
    order = db.query(models.Order).filter(models.Order.id == order_item.order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Check if order can be modified (only pending orders can be modified)
    if order.status != OrderStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify items in non-pending orders"
        )
    
    try:
        # If product_id is being updated, validate the new product
        if item_update.product_id is not None and item_update.product_id != order_item.product_id:
            new_product = db.query(models.Product).filter(models.Product.id == item_update.product_id).first()
            if not new_product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New product not found"
                )
            
            # Restore stock from old product
            old_product = db.query(models.Product).filter(models.Product.id == order_item.product_id).first()
            if old_product:
                old_product.stock += order_item.quantity
            
            # Check stock availability for new product
            if new_product.stock < (item_update.quantity or order_item.quantity):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient stock for new product"
                )
            
            # Update product_id and price
            order_item.product_id = item_update.product_id
            order_item.price = new_product.price
        
        # If quantity is being updated, handle stock changes
        if item_update.quantity is not None and item_update.quantity != order_item.quantity:
            product = db.query(models.Product).filter(models.Product.id == order_item.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product not found"
                )
            
            # Calculate stock difference
            quantity_diff = item_update.quantity - order_item.quantity
            
            # Check if we have enough stock for the increase
            if quantity_diff > 0 and product.stock < quantity_diff:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient stock for quantity increase"
                )
            
            # Update product stock
            product.stock -= quantity_diff
            order_item.quantity = item_update.quantity
        
        # Recalculate order total
        order_items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).all()
        new_total = sum(item.price * item.quantity for item in order_items)
        order.total_amount = new_total
        
        db.commit()
        db.refresh(order_item)
        return order_item
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order item"
        )

@app.delete("/order-item/{item_id}", status_code=status.HTTP_200_OK)
def delete_order_item(item_id: int, db: Session = Depends(get_db)):
    """Delete order item"""
    if item_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item ID must be > 0")
    
    order_item = db.query(models.OrderItem).filter(models.OrderItem.id == item_id).first()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")
    
    # Get the order to check if it can be modified
    order = db.query(models.Order).filter(models.Order.id == order_item.order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Check if order can be modified (only pending orders can be modified)
    if order.status != OrderStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete items in non-pending orders"
        )
    
    try:
        # Restore product stock
        product = db.query(models.Product).filter(models.Product.id == order_item.product_id).first()
        if product:
            product.stock += order_item.quantity
        
        # Recalculate order total
        remaining_items = db.query(models.OrderItem).filter(
            models.OrderItem.order_id == order.id,
            models.OrderItem.id != item_id
        ).all()
        
        if remaining_items:
            new_total = sum(item.price * item.quantity for item in remaining_items)
            order.total_amount = new_total
        else:
            # If no items left, delete the entire order
            db.delete(order)
            db.commit()
            return {"message": f"Order item with ID {item_id} deleted. Order was empty and has been deleted."}
        
        # Delete the order item
        db.delete(order_item)
        db.commit()
        return {"message": f"Order item with ID {item_id} successfully deleted"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete order item"
        )