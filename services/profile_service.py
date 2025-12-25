from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.models import Profile, Tag, Group, User
from core.schemas import ProfileCreate, ProfileUpdate
from datetime import datetime

class ProfileService:
    
    async def get_all_profiles(
        self,
        db: Session,
        user_id: int,
        page: int = 1,
        limit: int = 25,
        group: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict:
        """Get paginated list of profiles with filtering"""
        try:
            # Base query
            query = db.query(Profile).filter(Profile.owner_id == user_id)
            
            # Apply filters
            if group and group != "All Groups":
                query = query.join(Profile.groups).filter(Group.group_name == group)
            
            if tag and tag != "All Tags":
                query = query.join(Profile.tags).filter(Tag.name == tag)
            
            if search:
                search_term = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        Profile.name.ilike(search_term),
                        Profile.platform.ilike(search_term),
                        Profile.note.ilike(search_term)
                    )
                )
            
            if status and status != "all":
                query = query.filter(Profile.status == status)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            profiles = query.offset(offset).limit(limit).all()
            
            # Get all groups and tags for this user
            groups = db.query(Group).join(Group.profiles).filter(Profile.owner_id == user_id).distinct().all()
            tags = db.query(Tag).join(Tag.profiles).filter(Profile.owner_id == user_id).distinct().all()
            
            return {
                "success": True,
                "data": {
                    "profiles": profiles,
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit,
                    "groups": [g.group_name for g in groups],
                    "tags": [t.name for t in tags]
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Error getting profiles: {str(e)}"}
    
    async def create_profile(self, db: Session, user_id: int, profile_data: ProfileCreate) -> Dict:
        """Create a new profile"""
        try:
            # Create profile
            profile = Profile(
                name=profile_data.name,
                platform=profile_data.platform,
                note=profile_data.note,
                proxy=profile_data.proxy,
                owner_id=user_id
            )
            
            db.add(profile)
            db.flush()  # Get the ID
            
            # Handle groups
            if profile_data.groups:
                for group_name in profile_data.groups:
                    group = db.query(Group).filter(Group.group_name == group_name).first()
                    if not group:
                        group = Group(group_name=group_name)
                        db.add(group)
                        db.flush()
                    profile.groups.append(group)
            
            # Handle tags
            if profile_data.tags:
                for tag_name in profile_data.tags:
                    tag = db.query(Tag).filter(Tag.name == tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.add(tag)
                        db.flush()
                    profile.tags.append(tag)
            
            db.commit()
            db.refresh(profile)
            
            return {"success": True, "data": profile}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error creating profile: {str(e)}"}
    
    async def update_profile(self, db: Session, user_id: int, profile_id: int, profile_data: ProfileUpdate) -> Dict:
        """Update an existing profile"""
        try:
            profile = db.query(Profile).filter(
                and_(Profile.id == profile_id, Profile.owner_id == user_id)
            ).first()
            
            if not profile:
                return {"success": False, "message": "Profile not found"}
            
            # Update profile fields
            if profile_data.name is not None:
                profile.name = profile_data.name
            if profile_data.platform is not None:
                profile.platform = profile_data.platform
            if profile_data.note is not None:
                profile.note = profile_data.note
            if profile_data.proxy is not None:
                profile.proxy = profile_data.proxy
            if profile_data.status is not None:
                profile.status = profile_data.status
            if profile_data.shared_on_cloud is not None:
                profile.shared_on_cloud = profile_data.shared_on_cloud
            
            profile.updated_at = datetime.utcnow()
            
            # Update groups if provided
            if profile_data.groups is not None:
                profile.groups.clear()
                for group_name in profile_data.groups:
                    group = db.query(Group).filter(Group.group_name == group_name).first()
                    if not group:
                        group = Group(group_name=group_name)
                        db.add(group)
                        db.flush()
                    profile.groups.append(group)
            
            # Update tags if provided
            if profile_data.tags is not None:
                profile.tags.clear()
                for tag_name in profile_data.tags:
                    tag = db.query(Tag).filter(Tag.name == tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.add(tag)
                        db.flush()
                    profile.tags.append(tag)
            
            db.commit()
            db.refresh(profile)
            
            return {"success": True, "data": profile}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error updating profile: {str(e)}"}
    
    async def delete_profiles(self, db: Session, user_id: int, profile_ids: List[int]) -> Dict:
        """Delete multiple profiles"""
        try:
            deleted_count = db.query(Profile).filter(
                and_(Profile.id.in_(profile_ids), Profile.owner_id == user_id)
            ).delete(synchronize_session=False)
            
            db.commit()
            
            return {
                "success": True,
                "data": {"deleted": deleted_count}
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error deleting profiles: {str(e)}"}
    
    async def get_profile_by_id(self, db: Session, user_id: int, profile_id: int) -> Dict:
        """Get a single profile by ID"""
        try:
            profile = db.query(Profile).filter(
                and_(Profile.id == profile_id, Profile.owner_id == user_id)
            ).first()
            
            if not profile:
                return {"success": False, "message": "Profile not found"}
            
            return {"success": True, "data": profile}
        except Exception as e:
            return {"success": False, "message": f"Error getting profile: {str(e)}"}
    
    async def start_profile(self, db: Session, user_id: int, profile_id: int) -> Dict:
        """Start a profile (update last_started_at and status)"""
        try:
            profile = db.query(Profile).filter(
                and_(Profile.id == profile_id, Profile.owner_id == user_id)
            ).first()
            
            if not profile:
                return {"success": False, "message": "Profile not found"}
            
            profile.last_started_at = datetime.utcnow()
            profile.status = "Running"
            profile.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(profile)
            
            return {"success": True, "data": profile}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error starting profile: {str(e)}"}
    
    async def stop_profile(self, db: Session, user_id: int, profile_id: int) -> Dict:
        """Stop a profile (update status)"""
        try:
            profile = db.query(Profile).filter(
                and_(Profile.id == profile_id, Profile.owner_id == user_id)
            ).first()
            
            if not profile:
                return {"success": False, "message": "Profile not found"}
            
            profile.status = "Ready"
            profile.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(profile)
            
            return {"success": True, "data": profile}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error stopping profile: {str(e)}"}
    
    async def duplicate_profile(self, db: Session, user_id: int, profile_id: int) -> Dict:
        """Duplicate an existing profile"""
        try:
            original = db.query(Profile).filter(
                and_(Profile.id == profile_id, Profile.owner_id == user_id)
            ).first()
            
            if not original:
                return {"success": False, "message": "Profile not found"}
            
            # Create duplicate
            duplicate = Profile(
                name=f"{original.name} (Copy)",
                platform=original.platform,
                note=original.note,
                proxy=original.proxy,
                owner_id=user_id
            )
            
            db.add(duplicate)
            db.flush()
            
            # Copy groups and tags
            for group in original.groups:
                duplicate.groups.append(group)
            
            for tag in original.tags:
                duplicate.tags.append(tag)
            
            db.commit()
            db.refresh(duplicate)
            
            return {"success": True, "data": duplicate}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error duplicating profile: {str(e)}"}
    
    async def get_profile_stats(self, db: Session, user_id: int) -> Dict:
        """Get profile statistics"""
        try:
            profiles = db.query(Profile).filter(Profile.owner_id == user_id).all()
            
            stats = {
                "total": len(profiles),
                "ready": len([p for p in profiles if p.status == "Ready"]),
                "running": len([p for p in profiles if p.status == "Running"]),
                "by_platform": {},
                "by_group": {},
                "by_tag": {},
                "shared_on_cloud": len([p for p in profiles if p.shared_on_cloud]),
                "last_started": None
            }
            
            # Count by platform
            for profile in profiles:
                platform = profile.platform or "Unknown"
                stats["by_platform"][platform] = stats["by_platform"].get(platform, 0) + 1
            
            # Count by group
            for profile in profiles:
                for group in profile.groups:
                    stats["by_group"][group.group_name] = stats["by_group"].get(group.group_name, 0) + 1
            
            # Count by tag
            for profile in profiles:
                for tag in profile.tags:
                    stats["by_tag"][tag.name] = stats["by_tag"].get(tag.name, 0) + 1
            
            # Find last started time
            started_profiles = [p for p in profiles if p.last_started_at]
            if started_profiles:
                stats["last_started"] = max(p.last_started_at for p in started_profiles)
            
            return {"success": True, "data": stats}
        except Exception as e:
            return {"success": False, "message": f"Error getting stats: {str(e)}"}
    
    async def bulk_update_profiles(
        self, 
        db: Session, 
        user_id: int, 
        profile_ids: List[int], 
        updates: Dict
    ) -> Dict:
        """Bulk update multiple profiles"""
        try:
            profiles = db.query(Profile).filter(
                and_(Profile.id.in_(profile_ids), Profile.owner_id == user_id)
            ).all()
            
            if not profiles:
                return {"success": False, "message": "No profiles found"}
            
            updated_count = 0
            
            for profile in profiles:
                # Update basic fields
                if "status" in updates:
                    profile.status = updates["status"]
                if "shared_on_cloud" in updates:
                    profile.shared_on_cloud = updates["shared_on_cloud"]
                
                # Update groups
                if "groups" in updates:
                    profile.groups.clear()
                    for group_name in updates["groups"]:
                        group = db.query(Group).filter(Group.group_name == group_name).first()
                        if not group:
                            group = Group(group_name=group_name)
                            db.add(group)
                            db.flush()
                        profile.groups.append(group)
                
                # Update tags
                if "tags" in updates:
                    profile.tags.clear()
                    for tag_name in updates["tags"]:
                        tag = db.query(Tag).filter(Tag.name == tag_name).first()
                        if not tag:
                            tag = Tag(name=tag_name)
                            db.add(tag)
                            db.flush()
                        profile.tags.append(tag)
                
                profile.updated_at = datetime.utcnow()
                updated_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "data": {"updated": updated_count}
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error bulk updating profiles: {str(e)}"}
    
    async def get_all_groups(self, db: Session, user_id: int) -> Dict:
        """Get all groups for user"""
        try:
            groups = db.query(Group).join(Group.profiles).filter(Profile.owner_id == user_id).distinct().all()
            return {
                "success": True,
                "data": [group.group_name for group in groups]
            }
        except Exception as e:
            return {"success": False, "message": f"Error getting groups: {str(e)}"}
    
    async def get_all_tags(self, db: Session, user_id: int) -> Dict:
        """Get all tags for user"""
        try:
            tags = db.query(Tag).join(Tag.profiles).filter(Profile.owner_id == user_id).distinct().all()
            return {
                "success": True,
                "data": [tag.name for tag in tags]
            }
        except Exception as e:
            return {"success": False, "message": f"Error getting tags: {str(e)}"}