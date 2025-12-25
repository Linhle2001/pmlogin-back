from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Association tables for many-to-many relationships
profile_group_table = Table(
    'profile_group',
    Base.metadata,
    Column('profile_id', Integer, ForeignKey('profiles.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True)
)

profile_tag_table = Table(
    'profile_tag', 
    Base.metadata,
    Column('profile_id', Integer, ForeignKey('profiles.id'), primary_key=True),
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
    profiles = relationship("Profile", back_populates="owner")
    proxies = relationship("Proxy", back_populates="owner")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profiles = relationship("Profile", secondary=profile_tag_table, back_populates="tags")
    proxies = relationship("Proxy", secondary=proxy_tag_table, back_populates="tags")

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profiles = relationship("Profile", secondary=profile_group_table, back_populates="groups")

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    platform = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    proxy = Column(String, nullable=True)  # JSON string or proxy reference
    status = Column(String, default="Ready")
    shared_on_cloud = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_started_at = Column(DateTime, nullable=True)
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="profiles")
    groups = relationship("Group", secondary=profile_group_table, back_populates="profiles")
    tags = relationship("Tag", secondary=profile_tag_table, back_populates="profiles")

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