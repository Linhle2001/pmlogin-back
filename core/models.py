from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Association tables for many-to-many relationships
profile_group_table = Table(
    'shared_profile_group',
    Base.metadata,
    Column('shared_profile_id', Integer, ForeignKey('shared_profiles.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True)
)

profile_tag_table = Table(
    'shared_profile_tag', 
    Base.metadata,
    Column('shared_profile_id', Integer, ForeignKey('shared_profiles.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

proxy_tag_table = Table(
    'proxy_tags',
    Base.metadata,
    Column('proxy_id', Integer, ForeignKey('proxies.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    hwid = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    profile_stats = relationship("ProfileStats", back_populates="owner", uselist=False)
    shared_profiles = relationship("SharedProfile", back_populates="owner")
    proxies = relationship("Proxy", back_populates="owner")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    shared_profiles = relationship("SharedProfile", secondary=profile_tag_table, back_populates="tags")
    proxies = relationship("Proxy", secondary=proxy_tag_table, back_populates="tags")

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    shared_profiles = relationship("SharedProfile", secondary=profile_group_table, back_populates="groups")

# Bảng thống kê profile của client (không lưu chi tiết profile)
class ProfileStats(Base):
    __tablename__ = "profile_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_profiles = Column(Integer, default=0)
    shared_profiles = Column(Integer, default=0)  # Số profile được share lên cloud
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="profile_stats")

# Bảng lưu profile được share lên cloud (chỉ khi client chọn shared_on_cloud=True)
class SharedProfile(Base):
    __tablename__ = "shared_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    client_profile_id = Column(String, nullable=False)  # ID của profile trên client
    name = Column(String, nullable=False)
    platform = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    proxy_info = Column(Text, nullable=True)  # JSON string chứa thông tin proxy
    status = Column(String, default="Ready")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_started_at = Column(DateTime, nullable=True)
    sync_version = Column(Integer, default=1)  # Version để sync
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="shared_profiles")
    groups = relationship("Group", secondary=profile_group_table, back_populates="shared_profiles")
    tags = relationship("Tag", secondary=profile_tag_table, back_populates="shared_profiles")

class Proxy(Base):
    __tablename__ = "proxies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, default="")
    password = Column(String, default="")
    type = Column(String, default="http")  # http, https, socks4, socks5
    status = Column(String, default="pending")  # pending, live, dead
    response_time = Column(Float, nullable=True)
    public_ip = Column(String, nullable=True)
    location = Column(String, nullable=True)
    fail_count = Column(Integer, default=0)
    last_tested = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="proxies")
    tags = relationship("Tag", secondary=proxy_tag_table, back_populates="proxies")