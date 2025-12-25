from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import os
from dotenv import load_dotenv

from core.database import get_db, init_db
from core.models import User, Proxy, SharedProfile, ProfileStats, Tag, Group
from core.schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse, ChangePassword, 
    ProxyCreate, ProxyUpdate, ProxyTest, ProxyImport, ProxyResponse,
    ProfileCreate, ProfileUpdate, ProfileResponse,
    GenericResponse, PaginatedResponse
)
from core.auth import create_access_token, verify_token, get_password_hash, verify_password
from services.proxy_service import ProxyService
from services.profile_service import ProfileService
from services.original_server_service import original_server

# Load environment variables
load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "PM Login Backend"),
    version=os.getenv("VERSION", "1.0.0"),
    description="Backend API for PM Login Electron App"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Services will be initialized per request
# proxy_service = ProxyService()
# profile_service = ProfileService()

# Helper functions to get services
def get_proxy_service():
    return ProxyService()

def get_profile_service(db: Session):
    return ProfileService(db)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

# Auth endpoints
@app.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login endpoint - authenticates with local database"""
    
    try:
        # Validate input data
        if not user_data.email or not user_data.email.strip():
            return {
                "success": False,
                "message": "Email is required.",
                "error_code": "EMAIL_REQUIRED"
            }
        
        if not user_data.password or not user_data.password.strip():
            return {
                "success": False,
                "message": "Password is required.",
                "error_code": "PASSWORD_REQUIRED"
            }
        
        # Find user by email in local database
        user = db.query(User).filter(User.email == user_data.email.strip().lower()).first()
        if not user:
            return {
                "success": False,
                "message": "User not found. Please check your email.",
                "error_code": "USER_NOT_FOUND"
            }
        
        # Check if user is active
        if not user.is_active:
            return {
                "success": False,
                "message": "Account has been deactivated. Please contact support.",
                "error_code": "ACCOUNT_DEACTIVATED"
            }
        
        # Verify password
        if not verify_password(user_data.password, user.hashed_password):
            return {
                "success": False,
                "message": "Invalid password.",
                "error_code": "INVALID_PASSWORD"
            }
        
        # Check HWID if provided
        if user_data.hwid:
            if user.hwid is None:
                # Lần đăng nhập đầu tiên, lưu HWID
                user.hwid = user_data.hwid
            elif user.hwid != user_data.hwid:
                # HWID không khớp, từ chối đăng nhập
                return {
                    "success": False,
                    "message": "Hardware ID không khớp. Vui lòng đăng nhập từ thiết bị đã đăng ký.",
                    "error_code": "HWID_MISMATCH"
                }
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "is_active": user.is_active
                }
            }
        }
    
    except Exception as e:
        print(f"Login error: {e}")
        return {
            "success": False,
            "message": "Internal server error. Please try again later.",
            "error_code": "INTERNAL_ERROR"
        }

@app.post("/register", response_model=dict)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user - forwards to original server"""
    
    # Register with original server
    register_result = await original_server.register_user(user_data.email, user_data.password)
    
    if not register_result["success"]:
        return {
            "success": False,
            "message": register_result["data"].get("message", "Registration failed")
        }
    
    # Registration successful with original server
    original_data = register_result["data"].get("data", {})
    original_user_data = original_data.get("user", {})
    
    # Create user in local database
    user = User(
        email=user_data.email,
        hashed_password="",  # We don't store password
        created_at=datetime.utcnow(),
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "message": "User registered successfully",
        "data": {
            "user": {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "original_user_data": original_user_data
            }
        }
    }

@app.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token"""
    
    access_token = create_access_token(data={"sub": str(current_user.id)})
    
    return {
        "success": True,
        "message": "Token refreshed successfully",
        "data": {
            "access_token": access_token,
            "token_type": "bearer"
        }
    }

@app.get("/api/user", response_model=UserResponse)
async def get_user(current_user: User = Depends(get_current_user)):
    """Get current user data"""
    
    return {
        "success": True,
        "message": "User data retrieved successfully",
        "data": {
            "id": current_user.id,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat(),
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "is_active": current_user.is_active
        }
    }

@app.post("/change-password", response_model=dict)
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password - forwards to original server"""
    
    try:
        # Change password on the original server
        import aiohttp
        async with aiohttp.ClientSession() as session:
            change_payload = {
                "current_password": password_data.current_password,
                "password": password_data.password,
                "password_confirmation": password_data.password_confirmation
            }
            
            # Note: You might need to include the original token here
            # For now, we'll just forward the request
            async with session.post(
                "https://dev.pmbackend.site/change-password",
                json=change_payload,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("success"):
                    return {
                        "success": True,
                        "message": "Password changed successfully"
                    }
                else:
                    return {
                        "success": False,
                        "message": result.get("message", "Password change failed")
                    }
                    
    except aiohttp.ClientError:
        return {
            "success": False,
            "message": "Server không khả dụng. Vui lòng thử lại sau."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi kết nối: {str(e)}"
        }

# Proxy Management Endpoints (matching pmlogin-app IPC structure)
@app.post("/api/proxy/get-all")
async def proxy_get_all(
    options: Optional[dict] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all proxies with filtering options (matches proxy:get-all IPC)"""
    if options is None:
        options = {}
    
    result = await proxy_service.get_all_proxies(
        db, current_user.id, 
        page=options.get("page", 1),
        limit=options.get("limit", 25),
        tag=options.get("tag"),
        search=options.get("search"),
        status=options.get("status")
    )
    return result

@app.post("/api/proxy/add")
async def proxy_add(
    proxy_data: ProxyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new proxy (matches proxy:add IPC)"""
    result = await proxy_service.add_proxy(db, current_user.id, proxy_data)
    return result

@app.post("/api/proxy/update")
async def proxy_update(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing proxy (matches proxy:update IPC)"""
    proxy_id = request.get("id")
    proxy_data = ProxyUpdate(**request.get("data", {}))
    result = await proxy_service.update_proxy(db, current_user.id, proxy_id, proxy_data)
    return result

@app.post("/api/proxy/delete-multiple")
async def proxy_delete_multiple(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete multiple proxies (matches proxy:delete-multiple IPC)"""
    proxy_ids = request.get("ids", [])
    result = await proxy_service.delete_proxies(db, current_user.id, proxy_ids)
    return result

@app.post("/api/proxy/test")
async def proxy_test(proxy_data: ProxyTest):
    """Test a single proxy (matches proxy:test IPC)"""
    result = await proxy_service.test_proxy(proxy_data)
    return result

@app.post("/api/proxy/test-multiple")
async def proxy_test_multiple(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test multiple proxies (matches proxy:test-multiple IPC)"""
    proxy_ids = request.get("proxyIds", [])
    result = await proxy_service.test_proxies(db, current_user.id, proxy_ids)
    return result

@app.post("/api/proxy/import")
async def proxy_import(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import proxies from text (matches proxy:import IPC)"""
    proxy_text = request.get("proxyText", "")
    tags = request.get("tags", ["Default"])
    result = await proxy_service.import_proxies(db, current_user.id, proxy_text, tags)
    return result

@app.post("/api/proxy/export")
async def proxy_export(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export proxies (matches proxy:export IPC)"""
    format_type = request.get("format", "json")
    # Implementation for export
    return {"success": True, "data": "Export functionality", "filename": f"proxies.{format_type}"}

@app.post("/api/proxy/copy-selected")
async def proxy_copy_selected(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Copy selected proxies (matches proxy:copy-selected IPC)"""
    proxy_ids = request.get("proxyIds", [])
    
    # Get proxies by IDs
    proxies = db.query(Proxy).filter(
        Proxy.id.in_(proxy_ids),
        Proxy.owner_id == current_user.id
    ).all()
    
    proxy_lines = []
    for proxy in proxies:
        auth = f"{proxy.username}:{proxy.password}@" if proxy.username and proxy.password else ""
        proxy_lines.append(f"{proxy.type}://{auth}{proxy.host}:{proxy.port}")
    
    return {
        "success": True,
        "data": "\n".join(proxy_lines)
    }

# Profile Management Endpoints (matching pmlogin-app IPC structure)
@app.post("/api/profile/get-all")
async def profile_get_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all profiles (matches profile:get-all IPC)"""
    result = await profile_service.get_all_profiles(db, current_user.id)
    return result

@app.post("/api/profile/add")
async def profile_add(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new profile (matches profile:add IPC)"""
    result = await profile_service.create_profile(db, current_user.id, profile_data)
    return result

@app.post("/api/create-profile")
async def create_profile_handler(
    profile_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create profile handler (matches create-profile IPC)"""
    # Convert dict to ProfileCreate schema
    profile_create = ProfileCreate(
        name=profile_data.get("name"),
        platform=profile_data.get("platform", "windows"),
        note=profile_data.get("note", ""),
        proxy=profile_data.get("proxy"),
        groups=profile_data.get("groups", []),
        tags=profile_data.get("tags", [])
    )
    
    result = await profile_service.create_profile(db, current_user.id, profile_create)
    return result

@app.post("/api/get-profile")
async def get_profile_handler(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single profile (matches get-profile IPC)"""
    profile_id = request.get("profileId")
    result = await profile_service.get_profile_by_id(db, current_user.id, profile_id)
    return result

@app.post("/api/update-profile")
async def update_profile_handler(
    profile_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile handler (matches update-profile IPC)"""
    profile_id = profile_data.get("id")
    
    # Convert dict to ProfileUpdate schema
    profile_update = ProfileUpdate(
        name=profile_data.get("name"),
        platform=profile_data.get("platform"),
        note=profile_data.get("note"),
        proxy=profile_data.get("proxy"),
        groups=profile_data.get("groups"),
        tags=profile_data.get("tags")
    )
    
    result = await profile_service.update_profile(db, current_user.id, profile_id, profile_update)
    return result

# Database Management Endpoints (matching pmlogin-app IPC structure)
@app.post("/api/db/stats")
async def db_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get database statistics (matches db:stats IPC)"""
    try:
        # Import models to avoid name errors
        from core.models import Tag, Group
        
        # Get counts from database
        proxy_count = db.query(Proxy).filter(Proxy.owner_id == current_user.id).count()
        profile_count = db.query(SharedProfile).filter(SharedProfile.owner_id == current_user.id).count()
        tag_count = db.query(Tag).count()
        group_count = db.query(Group).count()
        
        stats = {
            "proxies": proxy_count,
            "profiles": profile_count,
            "tags": tag_count,
            "groups": group_count,
            "database_size": "N/A",  # Could implement actual size calculation
            "last_backup": None
        }
        
        return {"success": True, "data": stats}
    except Exception as e:
        return {"success": False, "message": f"Error getting database stats: {str(e)}"}

@app.post("/api/db/test")
async def db_test(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test database connection (matches db:test IPC)"""
    try:
        # Simple test query
        db.execute("SELECT 1")
        return {"success": True, "message": "Database test completed successfully"}
    except Exception as e:
        return {"success": False, "message": f"Database test failed: {str(e)}"}

# Database Proxy Endpoints
@app.post("/api/db/proxy/add")
async def db_proxy_add(
    proxy_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add proxy to database (matches db:proxy:add IPC)"""
    try:
        proxy_create = ProxyCreate(**proxy_data)
        result = await proxy_service.add_proxy(db, current_user.id, proxy_create)
        if result["success"]:
            return {"success": True, "data": {"id": result["data"].id}}
        return result
    except Exception as e:
        return {"success": False, "message": f"Error adding proxy to database: {str(e)}"}

@app.post("/api/db/proxy/get-all")
async def db_proxy_get_all(
    request: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all proxies from database (matches db:proxy:get-all IPC)"""
    try:
        tag_id = request.get("tagId") if request else None
        # If tag_id is provided, filter by tag
        query = db.query(Proxy).filter(Proxy.owner_id == current_user.id)
        if tag_id:
            query = query.join(Proxy.tags).filter(Tag.id == tag_id)
        
        proxies = query.all()
        return {"success": True, "data": proxies}
    except Exception as e:
        return {"success": False, "message": f"Error getting proxies from database: {str(e)}"}

@app.post("/api/db/proxy/get-live")
async def db_proxy_get_live(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get live proxies from database (matches db:proxy:get-live IPC)"""
    try:
        proxies = db.query(Proxy).filter(
            Proxy.owner_id == current_user.id,
            Proxy.status == "live"
        ).all()
        return {"success": True, "data": proxies}
    except Exception as e:
        return {"success": False, "message": f"Error getting live proxies from database: {str(e)}"}

# Database Tag Endpoints
@app.post("/api/db/tag/get-all")
async def db_tag_get_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tags from database (matches db:tag:get-all IPC)"""
    try:
        tags = db.query(Tag).all()
        return {"success": True, "data": tags}
    except Exception as e:
        return {"success": False, "message": f"Error getting tags from database: {str(e)}"}

@app.post("/api/db/tag/create")
async def db_tag_create(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create tag in database (matches db:tag:create IPC)"""
    try:
        tag_name = request.get("tagName")
        
        # Check if tag already exists
        existing_tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if existing_tag:
            return {"success": True, "data": {"id": existing_tag.id}}
        
        # Create new tag
        tag = Tag(name=tag_name)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        
        return {"success": True, "data": {"id": tag.id}}
    except Exception as e:
        return {"success": False, "message": f"Error creating tag: {str(e)}"}

# Database Group Endpoints
@app.post("/api/db/group/get-all")
async def db_group_get_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all groups from database (matches db:group:get-all IPC)"""
    try:
        groups = db.query(Group).all()
        return {"success": True, "data": groups}
    except Exception as e:
        return {"success": False, "message": f"Error getting groups from database: {str(e)}"}

@app.post("/api/db/group/create")
async def db_group_create(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create group in database (matches db:group:create IPC)"""
    try:
        group_name = request.get("groupName")
        
        # Check if group already exists
        existing_group = db.query(Group).filter(Group.group_name == group_name).first()
        if existing_group:
            return {"success": True, "data": {"id": existing_group.id}}
        
        # Create new group
        group = Group(group_name=group_name)
        db.add(group)
        db.commit()
        db.refresh(group)
        
        return {"success": True, "data": {"id": group.id}}
    except Exception as e:
        return {"success": False, "message": f"Error creating group: {str(e)}"}

# Database Profile Endpoints
@app.post("/api/db/profile/add")
async def db_profile_add(
    profile_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add profile to database (matches db:profile:add IPC)"""
    try:
        profile_create = ProfileCreate(**profile_data)
        result = await profile_service.create_profile(db, current_user.id, profile_create)
        if result["success"]:
            return {"success": True, "data": {"id": result["data"].id}}
        return result
    except Exception as e:
        return {"success": False, "message": f"Error adding profile to database: {str(e)}"}

@app.post("/api/db/profile/get-all")
async def db_profile_get_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all profiles from database (matches db:profile:get-all IPC)"""
    try:
        profiles = db.query(SharedProfile).filter(SharedProfile.owner_id == current_user.id).all()
        return {"success": True, "data": profiles}
    except Exception as e:
        return {"success": False, "message": f"Error getting profiles from database: {str(e)}"}

@app.post("/api/db/profile/get-local")
async def db_profile_get_local(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get local profiles from database (matches db:profile:get-local IPC)"""
    try:
        # For SharedProfile, all profiles are considered "local" since they're stored locally
        # but shared to cloud when needed
        profiles = db.query(SharedProfile).filter(SharedProfile.owner_id == current_user.id).all()
        return {"success": True, "data": profiles}
    except Exception as e:
        return {"success": False, "message": f"Error getting local profiles from database: {str(e)}"}

@app.post("/api/db/profile/get-cloud")
async def db_profile_get_cloud(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cloud profiles from database (matches db:profile:get-cloud IPC)"""
    try:
        # For SharedProfile, all profiles are considered "cloud" profiles
        profiles = db.query(SharedProfile).filter(SharedProfile.owner_id == current_user.id).all()
        return {"success": True, "data": profiles}
    except Exception as e:
        return {"success": False, "message": f"Error getting cloud profiles from database: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Error getting cloud profiles from database: {str(e)}"}

# Authentication Endpoints (matching pmlogin-app IPC structure)

@app.post("/api/auth/logout")
async def auth_logout():
    """Logout endpoint (matches auth:logout IPC)"""
    return {"success": True, "message": "Logged out successfully"}

@app.post("/api/auth/change-password")
async def auth_change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password endpoint (matches auth:change-password IPC)"""
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        return {
            "success": False,
            "message": "Current password is incorrect"
        }
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.password)
    db.commit()
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }

# User Data Endpoints
@app.post("/api/user/get-data")
async def user_get_data(current_user: User = Depends(get_current_user)):
    """Get user data (matches user:get-data IPC)"""
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat(),
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "is_active": current_user.is_active
        },
        "token": "current-token"  # In real implementation, you'd get this from the request
    }

# System Endpoints
@app.post("/api/system/info")
async def system_info():
    """Get system information (matches system:info IPC)"""
    import platform
    import uuid
    
    # Generate a simple hardware ID for demo
    hwid = str(uuid.uuid4())[:16]
    
    return {
        "version": "1.0.0",
        "hwid": hwid,
        "platform": platform.system().lower(),
        "arch": platform.machine(),
        "systemInfo": {
            "os": platform.system(),
            "version": platform.version(),
            "processor": platform.processor()
        }
    }

@app.post("/api/system/check-updates")
async def system_check_updates():
    """Check for updates (matches system:check-updates IPC)"""
    return {
        "success": True,
        "data": {
            "update_available": False,
            "latest_version": "1.0.0",
            "current_version": "1.0.0",
            "changelog": "No updates available"
        }
    }

# Navigation Endpoints
@app.post("/api/nav/to-main")
async def nav_to_main():
    """Navigate to main (matches nav:to-main IPC)"""
    return {"success": True, "message": "Navigation to main page"}

@app.post("/api/nav/to-login")
async def nav_to_login():
    """Navigate to login (matches nav:to-login IPC)"""
    return {"success": True, "message": "Navigation to login page"}

# File Operation Endpoints
@app.post("/api/file/select")
async def file_select(options: dict):
    """File select dialog (matches file:select IPC)"""
    # This would normally open a file dialog, but in web context we return a placeholder
    return {
        "canceled": False,
        "filePaths": ["/path/to/selected/file.txt"]
    }

@app.post("/api/file/save")
async def file_save(options: dict):
    """File save dialog (matches file:save IPC)"""
    # This would normally open a save dialog, but in web context we return a placeholder
    return {
        "canceled": False,
        "filePath": "/path/to/save/file.txt"
    }

# Notification Endpoint
@app.post("/api/notification/show")
async def notification_show(notification_data: dict):
    """Show notification (matches notification:show IPC)"""
    title = notification_data.get("title", "")
    body = notification_data.get("body", "")
    
    # In a real implementation, you might use web push notifications or websockets
    print(f"Notification: {title} - {body}")
    
    return {"success": True, "message": "Notification sent"}

@app.get("/api/info/plans", response_model=dict)
async def get_plans():
    """Get subscription plans from original server"""
    
    plans_result = await original_server.get_plans()
    
    if plans_result["success"]:
        return plans_result["data"]
    else:
        # Fallback to local plans if original server is unavailable
        plans = [
            {
                "id": 1,
                "name": "Basic",
                "price": 29.99,
                "duration": "monthly",
                "features": ["100 profiles", "Basic proxy support", "Email support"]
            },
            {
                "id": 2,
                "name": "Pro",
                "price": 59.99,
                "duration": "monthly", 
                "features": ["500 profiles", "Advanced proxy support", "Priority support", "API access"]
            },
            {
                "id": 3,
                "name": "Enterprise",
                "price": 199.99,
                "duration": "monthly",
                "features": ["Unlimited profiles", "Premium proxy support", "24/7 support", "Full API access", "Custom integrations"]
            }
        ]
        
        return {
            "success": True,
            "message": "Plans retrieved successfully (local fallback)",
            "data": plans
        }

@app.get("/api/info/system", response_model=dict)
async def get_system_info():
    """Get system information from original server"""
    
    system_result = await original_server.get_system_info()
    
    if system_result["success"]:
        return system_result["data"]
    else:
        # Fallback to local system info if original server is unavailable
        return {
            "success": True,
            "message": "System info retrieved successfully (local fallback)",
            "data": {
                "server_status": "online",
                "server_time": datetime.utcnow().isoformat(),
                "app_update": {
                    "latest_version": "1.0.1",
                    "current_version": "1.0.0",
                    "update_available": True,
                    "force_update": False,
                    "update_url": "https://github.com/your-repo/releases/latest",
                    "changelog": "Bug fixes and performance improvements"
                },
                "maintenance": {
                    "scheduled": False,
                    "message": None
                }
            }
        }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("VERSION", "1.0.0")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )