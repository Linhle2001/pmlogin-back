"""
API Routes - Endpoints để sync dữ liệu giữa client và server
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from core.database import get_db
from core.models import User, ProfileStats, SharedProfile
from services.profile_service import ProfileService, get_profile_service
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

# === Request/Response Models ===

class ProfileStatsRequest(BaseModel):
    total_profiles: int
    shared_profiles: int

class ProfileData(BaseModel):
    id: str
    name: str
    platform: str = None
    note: str = None
    proxy: Dict[str, Any] = None
    status: str = "Ready"
    last_started_at: str = None
    groups: List[str] = []
    tags: List[str] = []

class BulkSyncRequest(BaseModel):
    profiles: List[ProfileData]

class SyncResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any] = {}

# === Profile Stats Endpoints ===

@router.post("/sync-stats", response_model=SyncResponse)
async def sync_profile_stats(
    stats_data: ProfileStatsRequest,
    current_user: User = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Sync profile counts từ client"""
    try:
        stats = profile_service.update_profile_count(
            user_id=current_user.id,
            total_profiles=stats_data.total_profiles,
            shared_profiles=stats_data.shared_profiles
        )
        
        return SyncResponse(
            status="success",
            message="Profile stats synced successfully",
            data={
                "total_profiles": stats.total_profiles,
                "shared_profiles": stats.shared_profiles,
                "last_sync_at": stats.last_sync_at.isoformat() if stats.last_sync_at else None
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync profile stats: {str(e)}"
        )

@router.get("/sync-stats", response_model=SyncResponse)
async def get_profile_stats(
    current_user: User = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Lấy thống kê profile của user"""
    try:
        stats = profile_service.get_profile_stats(current_user.id)
        
        if not stats:
            return SyncResponse(
                status="success",
                message="No profile stats found",
                data={
                    "total_profiles": 0,
                    "shared_profiles": 0,
                    "last_sync_at": None
                }
            )
        
        return SyncResponse(
            status="success",
            message="Profile stats retrieved successfully",
            data={
                "total_profiles": stats.total_profiles,
                "shared_profiles": stats.shared_profiles,
                "last_sync_at": stats.last_sync_at.isoformat() if stats.last_sync_at else None,
                "created_at": stats.created_at.isoformat(),
                "updated_at": stats.updated_at.isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile stats: {str(e)}"
        )

# === Shared Profile Endpoints ===

@router.post("/sync-shared", response_model=SyncResponse)
async def sync_shared_profiles(
    sync_data: BulkSyncRequest,
    current_user: User = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Sync nhiều shared profiles từ client"""
    try:
        profiles_data = [profile.dict() for profile in sync_data.profiles]
        results = profile_service.bulk_sync_shared_profiles(current_user.id, profiles_data)
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = len(results) - success_count
        
        return SyncResponse(
            status="success",
            message=f"Synced {success_count} profiles successfully, {error_count} errors",
            data={
                "synced": success_count,
                "errors": error_count,
                "results": results
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync shared profiles: {str(e)}"
        )

@router.post("/sync-single", response_model=SyncResponse)
async def sync_single_profile(
    profile_data: ProfileData,
    current_user: User = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Sync một profile từ client"""
    try:
        profile = profile_service.sync_shared_profile(current_user.id, profile_data.dict())
        
        return SyncResponse(
            status="success",
            message="Profile synced successfully",
            data={
                "server_id": profile.id,
                "client_profile_id": profile.client_profile_id,
                "name": profile.name,
                "sync_version": profile.sync_version,
                "updated_at": profile.updated_at.isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync profile: {str(e)}"
        )

@router.delete("/shared/{client_profile_id}", response_model=SyncResponse)
async def remove_shared_profile(
    client_profile_id: str,
    current_user: User = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Xóa shared profile khỏi server"""
    try:
        success = profile_service.remove_shared_profile(current_user.id, client_profile_id)
        
        if success:
            return SyncResponse(
                status="success",
                message="Shared profile removed successfully",
                data={"client_profile_id": client_profile_id}
            )
        else:
            return SyncResponse(
                status="not_found",
                message="Shared profile not found",
                data={"client_profile_id": client_profile_id}
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove shared profile: {str(e)}"
        )

@router.get("/shared", response_model=SyncResponse)
async def get_shared_profiles(
    current_user: User = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Lấy tất cả shared profiles của user"""
    try:
        profiles = profile_service.get_shared_profiles(current_user.id)
        
        profiles_data = []
        for profile in profiles:
            profiles_data.append({
                "id": profile.id,
                "client_profile_id": profile.client_profile_id,
                "name": profile.name,
                "platform": profile.platform,
                "note": profile.note,
                "proxy_info": profile.proxy_info,
                "status": profile.status,
                "sync_version": profile.sync_version,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat(),
                "last_started_at": profile.last_started_at.isoformat() if profile.last_started_at else None,
                "groups": [g.group_name for g in profile.groups],
                "tags": [t.name for t in profile.tags]
            })
        
        return SyncResponse(
            status="success",
            message=f"Retrieved {len(profiles)} shared profiles",
            data={
                "profiles": profiles_data,
                "count": len(profiles)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get shared profiles: {str(e)}"
        )

@router.get("/sync-summary", response_model=SyncResponse)
async def get_sync_summary(
    current_user: User = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """Lấy tóm tắt thông tin sync"""
    try:
        summary = profile_service.get_sync_summary(current_user.id)
        
        return SyncResponse(
            status="success",
            message="Sync summary retrieved successfully",
            data=summary
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync summary: {str(e)}"
        )

# === Health Check ===

@router.get("/health", response_model=SyncResponse)
async def health_check():
    """Health check endpoint"""
    return SyncResponse(
        status="success",
        message="Profile service is healthy",
        data={
            "timestamp": datetime.utcnow().isoformat(),
            "service": "profile_sync"
        }
    )