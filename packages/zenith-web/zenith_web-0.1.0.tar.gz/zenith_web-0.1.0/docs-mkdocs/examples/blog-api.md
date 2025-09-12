---
title: Blog API
description: Complete blog API with authentication, CRUD operations, and search
---


## Overview

This example demonstrates building a complete blog API with Zenith, featuring:

- **User Authentication** - Registration, login, JWT tokens
- **CRUD Operations** - Posts, comments, categories
- **Database Integration** - SQLModel with PostgreSQL
- **Search & Filtering** - Full-text search, pagination
- **File Uploads** - Image uploads for posts
- **API Documentation** - Automatic OpenAPI generation

## Project Structure

<FileTree>
- blog-api/
  - app/
    - __init__.py
    - main.py                **Entry point**
    - config.py              **Configuration**
    - models/               **Database models**
      - __init__.py
      - user.py
      - post.py
      - comment.py
      - category.py
    - contexts/             **Business logic**
      - __init__.py
      - auth.py
      - posts.py
      - comments.py
    - routes/               **API endpoints**
      - __init__.py
      - auth.py
      - posts.py
      - comments.py
      - categories.py
    - utils/
      - __init__.py
      - search.py
      - uploads.py
  - tests/
  - migrations/
  - uploads/
  - .env
  - requirements.txt
</FileTree>

## Database Models

### User Model

```python
# app/models/user.py
from zenith.db import SQLModel, Field
from sqlmodel import Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    AUTHOR = "author"
    READER = "reader"

class User(SQLModel, table=True):
    """User model for authentication and authorization."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Authentication
    password_hash: str
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    role: UserRole = Field(default=UserRole.READER)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    # Relationships
    posts: List["Post"] = Relationship(back_populates="author")
    comments: List["Comment"] = Relationship(back_populates="author")

# Request/Response models
class UserCreate(SQLModel):
    email: str = Field(regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    full_name: Optional[str] = None

class UserLogin(SQLModel):
    email: str
    password: str

class UserResponse(SQLModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    role: UserRole
    created_at: datetime
    posts_count: int = 0
```

### Post Model

```python
# app/models/post.py
from zenith.db import SQLModel, Field
from sqlmodel import Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class Post(SQLModel, table=True):
    """Blog post model."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    slug: str = Field(unique=True, index=True)
    excerpt: Optional[str] = None
    content: str
    featured_image: Optional[str] = None
    
    # Metadata
    status: PostStatus = Field(default=PostStatus.DRAFT)
    is_featured: bool = Field(default=False)
    views_count: int = Field(default=0)
    likes_count: int = Field(default=0)
    
    # SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    # Foreign keys
    author_id: int = Field(foreign_key="user.id")
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    
    # Relationships
    author: "User" = Relationship(back_populates="posts")
    category: Optional["Category"] = Relationship(back_populates="posts")
    comments: List["Comment"] = Relationship(back_populates="post")
    tags: List["Tag"] = Relationship(
        back_populates="posts",
        link_model="PostTag"
    )

# Request/Response models
class PostCreate(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    excerpt: Optional[str] = Field(max_length=500)
    category_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    status: PostStatus = PostStatus.DRAFT
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

class PostUpdate(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    status: Optional[PostStatus] = None
    is_featured: Optional[bool] = None

class PostResponse(SQLModel):
    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    content: str
    status: PostStatus
    featured_image: Optional[str]
    is_featured: bool
    views_count: int
    likes_count: int
    created_at: datetime
    published_at: Optional[datetime]
    author: UserResponse
    category: Optional["CategoryResponse"]
    tags: List[str]
    comments_count: int = 0
```

## Authentication Context

```python
# app/contexts/auth.py
from zenith import Context
from zenith.auth.password import hash_password, verify_password
from zenith.auth import create_access_token
from app.models.user import User, UserCreate, UserLogin
from sqlmodel import select
from typing import Optional
from datetime import datetime

class AuthContext(Context):
    """Authentication business logic."""
    
    async def register_user(self, user_data: UserCreate) -> dict:
        """Register a new user."""
        # Check if email exists
        existing = await self.get_user_by_email(user_data.email)
        if existing:
            raise ValueError("Email already registered")
        
        # Check if username exists
        existing = await self.get_user_by_username(user_data.username)
        if existing:
            raise ValueError("Username already taken")
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            password_hash=hash_password(user_data.password)
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        # Generate token
        token = create_access_token({
            "sub": user.email,
            "user_id": user.id,
            "role": user.role
        })
        
        return {
            "user": user,
            "access_token": token,
            "token_type": "bearer"
        }
    
    async def authenticate_user(self, credentials: UserLogin) -> dict:
        """Login user with email/password."""
        # Get user by email
        user = await self.get_user_by_email(credentials.email)
        if not user:
            raise ValueError("Invalid credentials")
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            raise ValueError("Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is deactivated")
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()
        
        # Generate token
        token = create_access_token({
            "sub": user.email,
            "user_id": user.id,
            "role": user.role
        })
        
        return {
            "user": user,
            "access_token": token,
            "token_type": "bearer"
        }
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        statement = select(User).where(User.email == email)
        result = await self.db.exec(statement)
        return result.first()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        statement = select(User).where(User.username == username)
        result = await self.db.exec(statement)
        return result.first()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return await self.db.get(User, user_id)
```

## Posts Context

```python
# app/contexts/posts.py
from zenith import Context
from app.models.post import Post, PostCreate, PostUpdate, PostStatus
from app.models.user import User
from sqlmodel import select, func, or_, and_
from typing import List, Optional
from datetime import datetime
import re

class PostsContext(Context):
    """Posts business logic."""
    
    async def create_post(self, post_data: PostCreate, author: User) -> Post:
        """Create a new blog post."""
        # Generate slug from title
        slug = self.generate_slug(post_data.title)
        
        # Ensure slug is unique
        slug = await self.ensure_unique_slug(slug)
        
        # Create post
        post = Post(
            title=post_data.title,
            slug=slug,
            content=post_data.content,
            excerpt=post_data.excerpt or self.generate_excerpt(post_data.content),
            category_id=post_data.category_id,
            status=post_data.status,
            meta_title=post_data.meta_title,
            meta_description=post_data.meta_description,
            author_id=author.id
        )
        
        # Set published date if published
        if post.status == PostStatus.PUBLISHED:
            post.published_at = datetime.utcnow()
        
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        
        # Handle tags
        if post_data.tags:
            await self.update_post_tags(post.id, post_data.tags)
        
        return post
    
    async def get_posts(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[PostStatus] = None,
        category_id: Optional[int] = None,
        author_id: Optional[int] = None,
        search: Optional[str] = None,
        featured_only: bool = False
    ) -> List[Post]:
        """Get posts with filtering and pagination."""
        statement = select(Post)
        
        # Apply filters
        conditions = []
        
        if status:
            conditions.append(Post.status == status)
        
        if category_id:
            conditions.append(Post.category_id == category_id)
        
        if author_id:
            conditions.append(Post.author_id == author_id)
        
        if featured_only:
            conditions.append(Post.is_featured == True)
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    Post.title.ilike(search_term),
                    Post.content.ilike(search_term),
                    Post.excerpt.ilike(search_term)
                )
            )
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        # Order by published date (newest first)
        statement = (
            statement.order_by(Post.published_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.exec(statement)
        return result.all()
    
    async def get_post_by_slug(self, slug: str) -> Optional[Post]:
        """Get post by slug."""
        statement = select(Post).where(Post.slug == slug)
        result = await self.db.exec(statement)
        post = result.first()
        
        # Increment view count
        if post:
            post.views_count += 1
            await self.db.commit()
        
        return post
    
    async def update_post(self, post_id: int, post_data: PostUpdate, author: User) -> Optional[Post]:
        """Update existing post."""
        post = await self.db.get(Post, post_id)
        if not post:
            return None
        
        # Check ownership or admin rights
        if post.author_id != author.id and author.role != "admin":
            raise PermissionError("Not authorized to edit this post")
        
        # Update fields
        update_data = post_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "tags":
                continue  # Handle tags separately
            setattr(post, field, value)
        
        # Update slug if title changed
        if post_data.title:
            new_slug = self.generate_slug(post_data.title)
            if new_slug != post.slug:
                post.slug = await self.ensure_unique_slug(new_slug, exclude_id=post.id)
        
        # Set published date if status changed to published
        if post_data.status == PostStatus.PUBLISHED and post.published_at is None:
            post.published_at = datetime.utcnow()
        
        post.updated_at = datetime.utcnow()
        
        # Handle tags
        if post_data.tags is not None:
            await self.update_post_tags(post.id, post_data.tags)
        
        await self.db.commit()
        await self.db.refresh(post)
        return post
    
    async def delete_post(self, post_id: int, author: User) -> bool:
        """Delete post."""
        post = await self.db.get(Post, post_id)
        if not post:
            return False
        
        # Check ownership or admin rights
        if post.author_id != author.id and author.role != "admin":
            raise PermissionError("Not authorized to delete this post")
        
        await self.db.delete(post)
        await self.db.commit()
        return True
    
    def generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title."""
        slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:50]  # Limit length
    
    async def ensure_unique_slug(self, slug: str, exclude_id: Optional[int] = None) -> str:
        """Ensure slug is unique by adding suffix if needed."""
        original_slug = slug
        counter = 1
        
        while True:
            statement = select(Post).where(Post.slug == slug)
            if exclude_id:
                statement = statement.where(Post.id != exclude_id)
            
            result = await self.db.exec(statement)
            if not result.first():
                return slug
            
            slug = f"{original_slug}-{counter}"
            counter += 1
    
    def generate_excerpt(self, content: str, length: int = 200) -> str:
        """Generate excerpt from content."""
        # Strip HTML tags (basic)
        text = re.sub(r'<[^>]+>', '', content)
        if len(text) <= length:
            return text
        return text[:length].rsplit(' ', 1)[0] + '...'
```

## API Routes

### Authentication Routes

```python
# app/routes/auth.py
from zenith import Router, Depends, HTTPException
from zenith.auth import get_current_user
from app.contexts.auth import AuthContext
from app.models.user import UserCreate, UserLogin, UserResponse

router = Router(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=dict)
async def register(
    user_data: UserCreate,
    auth: AuthContext = Depends()
):
    """Register a new user."""
    try:
        result = await auth.register_user(user_data)
        return {
            "message": "User registered successfully",
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "user": UserResponse.from_orm(result["user"])
        }
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/login", response_model=dict)
async def login(
    credentials: UserLogin,
    auth: AuthContext = Depends()
):
    """Login user."""
    try:
        result = await auth.authenticate_user(credentials)
        return {
            "message": "Login successful",
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "user": UserResponse.from_orm(result["user"])
        }
    except ValueError as e:
        raise HTTPException(401, str(e))

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """Get current user info."""
    return UserResponse.from_orm(current_user)

@router.post("/logout")
async def logout():
    """Logout user (client should discard token)."""
    return {"message": "Logged out successfully"}
```

### Posts Routes

```python
# app/routes/posts.py
from zenith import Router, Depends, HTTPException, Query
from zenith.auth import get_current_user
from app.contexts.posts import PostsContext
from app.models.post import PostCreate, PostUpdate, PostResponse, PostStatus
from app.models.user import User
from typing import List, Optional

router = Router(prefix="/posts", tags=["Posts"])

@router.get("/", response_model=List[PostResponse])
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[PostStatus] = None,
    category_id: Optional[int] = None,
    author_id: Optional[int] = None,
    search: Optional[str] = None,
    featured: bool = False,
    posts: PostsContext = Depends()
):
    """List posts with filtering and pagination."""
    posts_list = await posts.get_posts(
        skip=skip,
        limit=limit,
        status=status or PostStatus.PUBLISHED,
        category_id=category_id,
        author_id=author_id,
        search=search,
        featured_only=featured
    )
    return [PostResponse.from_orm(post) for post in posts_list]

@router.post("/", response_model=PostResponse, status_code=201)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    posts: PostsContext = Depends()
):
    """Create a new post."""
    post = await posts.create_post(post_data, current_user)
    return PostResponse.from_orm(post)

@router.get("/{slug}", response_model=PostResponse)
async def get_post(
    slug: str,
    posts: PostsContext = Depends()
):
    """Get post by slug."""
    post = await posts.get_post_by_slug(slug)
    if not post:
        raise HTTPException(404, "Post not found")
    return PostResponse.from_orm(post)

@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user),
    posts: PostsContext = Depends()
):
    """Update post."""
    try:
        post = await posts.update_post(post_id, post_data, current_user)
        if not post:
            raise HTTPException(404, "Post not found")
        return PostResponse.from_orm(post)
    except PermissionError as e:
        raise HTTPException(403, str(e))

@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    posts: PostsContext = Depends()
):
    """Delete post."""
    try:
        if not await posts.delete_post(post_id, current_user):
            raise HTTPException(404, "Post not found")
    except PermissionError as e:
        raise HTTPException(403, str(e))

@router.post("/{post_id}/like", status_code=204)
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    posts: PostsContext = Depends()
):
    """Like a post."""
    # Implementation for liking posts
    pass
```

## File Upload

```python
# app/routes/uploads.py
from zenith import Router, UploadFile, File, Depends, HTTPException
from zenith.auth import get_current_user
from app.models.user import User
import os
import uuid
from PIL import Image
from typing import List

router = Router(prefix="/uploads", tags=["File Uploads"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/images", response_model=dict)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload an image file."""
    # Validate file
    if not file.filename:
        raise HTTPException(400, "No file selected")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create thumbnail
    thumbnail_path = create_thumbnail(file_path)
    
    return {
        "filename": filename,
        "url": f"/static/uploads/{filename}",
        "thumbnail_url": f"/static/uploads/{os.path.basename(thumbnail_path)}",
        "size": len(content),
        "content_type": file.content_type
    }

def create_thumbnail(image_path: str, size: tuple = (300, 200)) -> str:
    """Create thumbnail from image."""
    with Image.open(image_path) as img:
        img.thumbnail(size, Image.LANCZOS)
        
        # Generate thumbnail filename
        base, ext = os.path.splitext(image_path)
        thumbnail_path = f"{base}_thumb{ext}"
        
        img.save(thumbnail_path)
        return thumbnail_path
```

## Application Setup

```python
# app/main.py
from zenith import Zenith
from zenith.middleware import (
    CORSMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    LoggingMiddleware
)
from app.config import settings
from app.routes import auth, posts, comments, categories, uploads
from app.models import *  # Import all models
from zenith.db import create_engine, SQLModel

# Create application
app = Zenith(
    title="Blog API",
    description="A complete blog API built with Zenith",
    version="1.0.0",
    debug=settings.DEBUG
)

# Database setup
engine = create_engine(settings.DATABASE_URL)

@app.on_event("startup")
async def startup():
    """Create database tables."""
    SQLModel.metadata.create_all(engine)

# Middleware
app.add_middleware(SecurityHeadersMiddleware, {
    "force_https": settings.FORCE_HTTPS
})

app.add_middleware(CORSMiddleware, {
    "allow_origins": settings.CORS_ORIGINS,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"]
})

app.add_middleware(RateLimitMiddleware, {
    "default_limits": ["100/minute", "1000/hour"]
})

app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(categories.router)
app.include_router(uploads.router)

# Static files
app.static("/static", directory="uploads")

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": app.version,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
```

## Testing

```python
# tests/test_posts.py
import pytest
from zenith.testing import TestClient
from app.main import app
from app.models.user import User
from app.models.post import Post, PostStatus

@pytest.mark.asyncio
async def test_create_post():
    async with TestClient(app) as client:
        # Register user
        register_response = await client.post("/auth/register", json={
            "email": "author@example.com",
            "username": "author",
            "password": "SecurePass123!",
            "full_name": "Test Author"
        })
        token = register_response.json()["access_token"]
        
        # Create post
        post_response = await client.post(
            "/posts",
            json={
                "title": "My First Post",
                "content": "This is the content of my first post.",
                "status": "published",
                "tags": ["zenith", "api"]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert post_response.status_code == 201
        post_data = post_response.json()
        assert post_data["title"] == "My First Post"
        assert post_data["slug"] == "my-first-post"
        assert post_data["status"] == "published"

@pytest.mark.asyncio
async def test_list_posts():
    async with TestClient(app) as client:
        response = await client.get("/posts")
        assert response.status_code == 200
        posts = response.json()
        assert isinstance(posts, list)

@pytest.mark.asyncio
async def test_get_post_by_slug():
    async with TestClient(app) as client:
        response = await client.get("/posts/my-first-post")
        assert response.status_code == 200
        post = response.json()
        assert post["title"] == "My First Post"
```

## Running the Application

**Development:**
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload

# Or use Zenith CLI
zen server --reload
```

**Production:**
```bash
# Install with production dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://..."
export SECRET_KEY="your-secret-key"
export ENVIRONMENT="production"

# Run migrations
alembic upgrade head

# Start with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**Docker:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app
    
    COPY requirements.txt .
    RUN pip install -r requirements.txt
    
    COPY . .
    
    EXPOSE 8000
    
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    ```
  </TabItem>
</Tabs>

<Aside type="tip">
  **Pro Tip**: This example demonstrates many Zenith features working together. You can use parts of it as a starting point for your own projects.
</Aside>

## API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

## Complete Code

Find the complete blog API example at:
[github.com/nijaru/zenith/examples/blog-api](https://github.com/nijaru/zenith/tree/main/examples/blog-api)

## Next Steps

- Add [WebSocket](/examples/chat) support for real-time features
- Implement [caching](/concepts/middleware#caching-middleware) for better performance
- Add [email notifications](/features/background-tasks) for new comments
- Deploy to [production](/deployment/docker) with Docker