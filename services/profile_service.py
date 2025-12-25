"""
Profile Service - Quản lý thống kê profile và shared profiles
Server chỉ lưu:
1. Số lượng profile của client (ProfileStats)
2. Chi tiết profile khi client chọn shared_on_cloud=True (SharedProfile)
"""

from sqlalchemy.orm import Session
from core.models import ProfileStats, SharedProfile, User, Group, Tag
from core.database import get_db
from datetime import datetime
import json
from typing import List, Optional, Dict, Any

class ProfileService:
    def __init__(self, db: Session):
        self.db = db

    # === Profile Stats Management ===
    
    def get_or_create_profile_stats(self, user_id: int) -> ProfileStats:
        """Lấy hoặc tạo profile stats cho user"""
        stats = self.db.query(ProfileStats).filter(ProfileStats.user_id == user_id).first()
        if not stats:
            stats = ProfileStats(user_id=user_id)
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(stats)
        return stats

    def update_profile_count(self, user_id: int, total_profiles: int, shared_profiles: int):
        """Cập nhật số lượng profile từ client"""
        stats = self.get_or_create_profile_stats(user_id)
        stats.total_profiles = total_profiles
        stats.shared_profiles = shared_profiles
        stats.last_sync_at = datetime.utcnow()
        stats.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(stats)
        return stats

    def get_profile_stats(self, user_id: int) -> Optional[ProfileStats]:
        """Lấy thống kê profile của user"""
        return self.db.query(ProfileStats).filter(ProfileStats.user_id == user_id).first()

    # === Shared Profile Management ===
    
    def sync_shared_profile(self, user_id: int, profile_data: Dict[str, Any]) -> SharedProfile:
        """Sync profile được share từ client lên server"""
        client_profile_id = str(profile_data.get('id'))
        
        # Tìm profile đã tồn tại
        existing_profile = self.db.query(SharedProfile).filter(
            SharedProfile.owner_id == user_id,
            SharedProfile.client_profile_id == client_profile_id
        ).first()
        
        if existing_profile:
            # Cập nhật profile hiện tại
            existing_profile.name = profile_data.get('name', existing_profile.name)
            existing_profile.platform = profile_data.get('platform')
            existing_profile.note = profile_data.get('note')
            existing_profile.proxy_info = json.dumps(profile_data.get('proxy')) if profile_data.get('proxy') else None
            existing_profile.status = profile_data.get('status', 'Ready')
            existing_profile.updated_at = datetime.utcnow()
            existing_profile.sync_version += 1
            
            if profile_data.get('last_started_at'):
                existing_profile.last_started_at = datetime.fromisoformat(profile_data['last_started_at'])
            
            profile = existing_profile
        else:
            # Tạo profile mới
            profile = SharedProfile(
                owner_id=user_id,
                client_profile_id=client_profile_id,
                name=profile_data.get('name', 'Unknown Profile'),
                platform=profile_data.get('platform'),
                note=profile_data.get('note'),
                proxy_info=json.dumps(profile_data.get('proxy')) if profile_data.get('proxy') else None,
                status=profile_data.get('status', 'Ready')
            )
            
            if profile_data.get('last_started_at'):
                profile.last_started_at = datetime.fromisoformat(profile_data['last_started_at'])
            
            self.db.add(profile)
        
        # Sync groups và tags nếu có
        if 'groups' in profile_data:
            self._sync_profile_groups(profile, profile_data['groups'])
        
        if 'tags' in profile_data:
            self._sync_profile_tags(profile, profile_data['tags'])
        
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def remove_shared_profile(self, user_id: int, client_profile_id: str):
        """Xóa shared profile khi client bỏ chọn shared_on_cloud"""
        profile = self.db.query(SharedProfile).filter(
            SharedProfile.owner_id == user_id,
            SharedProfile.client_profile_id == str(client_profile_id)
        ).first()
        
        if profile:
            self.db.delete(profile)
            self.db.commit()
            return True
        return False

    def get_shared_profiles(self, user_id: int) -> List[SharedProfile]:
        """Lấy tất cả shared profiles của user"""
        return self.db.query(SharedProfile).filter(
            SharedProfile.owner_id == user_id
        ).order_by(SharedProfile.updated_at.desc()).all()

    def get_shared_profile(self, user_id: int, client_profile_id: str) -> Optional[SharedProfile]:
        """Lấy một shared profile cụ thể"""
        return self.db.query(SharedProfile).filter(
            SharedProfile.owner_id == user_id,
            SharedProfile.client_profile_id == str(client_profile_id)
        ).first()

    # === Helper Methods ===
    
    def _sync_profile_groups(self, profile: SharedProfile, group_names: List[str]):
        """Sync groups cho profile"""
        # Xóa groups hiện tại
        profile.groups.clear()
        
        # Thêm groups mới
        for group_name in group_names:
            group = self.db.query(Group).filter(Group.group_name == group_name).first()
            if not group:
                group = Group(group_name=group_name)
                self.db.add(group)
                self.db.flush()  # Để có ID
            
            profile.groups.append(group)

    def _sync_profile_tags(self, profile: SharedProfile, tag_names: List[str]):
        """Sync tags cho profile"""
        # Xóa tags hiện tại
        profile.tags.clear()
        
        # Thêm tags mới
        for tag_name in tag_names:
            tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                self.db.add(tag)
                self.db.flush()  # Để có ID
            
            profile.tags.append(tag)

    # === Bulk Operations ===
    
    def bulk_sync_shared_profiles(self, user_id: int, profiles_data: List[Dict[str, Any]]):
        """Sync nhiều shared profiles cùng lúc"""
        results = []
        for profile_data in profiles_data:
            try:
                profile = self.sync_shared_profile(user_id, profile_data)
                results.append({
                    'client_profile_id': profile.client_profile_id,
                    'status': 'success',
                    'server_id': profile.id
                })
            except Exception as e:
                results.append({
                    'client_profile_id': profile_data.get('id'),
                    'status': 'error',
                    'error': str(e)
                })
        
        return results

    def get_sync_summary(self, user_id: int) -> Dict[str, Any]:
        """Lấy tóm tắt thông tin sync"""
        stats = self.get_profile_stats(user_id)
        shared_profiles = self.get_shared_profiles(user_id)
        
        return {
            'total_profiles': stats.total_profiles if stats else 0,
            'shared_profiles_count': stats.shared_profiles if stats else 0,
            'shared_profiles_on_server': len(shared_profiles),
            'last_sync_at': stats.last_sync_at.isoformat() if stats and stats.last_sync_at else None,
            'shared_profiles': [
                {
                    'id': p.id,
                    'client_profile_id': p.client_profile_id,
                    'name': p.name,
                    'platform': p.platform,
                    'status': p.status,
                    'sync_version': p.sync_version,
                    'updated_at': p.updated_at.isoformat()
                }
                for p in shared_profiles
            ]
        }

# Dependency injection helper
def get_profile_service(db: Session = None) -> ProfileService:
    if db is None:
        db = next(get_db())
    return ProfileService(db)