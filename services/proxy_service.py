import asyncio
import aiohttp
import time
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.models import Proxy, Tag, User
from core.schemas import ProxyCreate, ProxyUpdate, ProxyTest
import re
from urllib.parse import urlparse
from datetime import datetime

class ProxyService:
    def __init__(self):
        self.test_urls = [
            "https://httpbin.org/ip",
            "https://api.ipify.org?format=json", 
            "https://ifconfig.me/ip"
        ]
    
    async def get_all_proxies(
        self, 
        db: Session, 
        user_id: int,
        page: int = 1,
        limit: int = 25,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict:
        """Get paginated list of proxies with filtering"""
        try:
            # Base query
            query = db.query(Proxy).filter(Proxy.owner_id == user_id)
            
            # Apply filters
            if tag and tag != "All Tags":
                query = query.join(Proxy.tags).filter(Tag.name == tag)
            
            if search:
                search_term = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        Proxy.name.ilike(search_term),
                        Proxy.host.ilike(search_term),
                        Proxy.username.ilike(search_term)
                    )
                )
            
            if status and status != "all":
                query = query.filter(Proxy.status == status)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            proxies = query.offset(offset).limit(limit).all()
            
            # Get all tags for this user
            tags = db.query(Tag).join(Tag.proxies).filter(Proxy.owner_id == user_id).distinct().all()
            tag_names = [tag.name for tag in tags]
            
            return {
                "success": True,
                "data": {
                    "proxies": proxies,
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit,
                    "tags": tag_names
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Error getting proxies: {str(e)}"}
    
    async def add_proxy(self, db: Session, user_id: int, proxy_data: ProxyCreate) -> Dict:
        """Add a new proxy"""
        try:
            # Validate proxy data
            validation = self._validate_proxy_data(proxy_data)
            if not validation["valid"]:
                return {"success": False, "message": validation["message"]}
            
            # Create proxy
            proxy = Proxy(
                host=proxy_data.host.strip(),
                port=proxy_data.port,
                username=proxy_data.username.strip() if proxy_data.username else "",
                password=proxy_data.password.strip() if proxy_data.password else "",
                type=proxy_data.type,
                name=proxy_data.name or f"{proxy_data.host}:{proxy_data.port}",
                owner_id=user_id
            )
            
            db.add(proxy)
            db.flush()  # Get the ID
            
            # Handle tags
            if proxy_data.tags:
                for tag_name in proxy_data.tags:
                    tag = db.query(Tag).filter(Tag.name == tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.add(tag)
                        db.flush()
                    proxy.tags.append(tag)
            
            db.commit()
            db.refresh(proxy)
            
            return {"success": True, "data": proxy}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error adding proxy: {str(e)}"}
    
    async def update_proxy(self, db: Session, user_id: int, proxy_id: int, proxy_data: ProxyUpdate) -> Dict:
        """Update an existing proxy"""
        try:
            proxy = db.query(Proxy).filter(
                and_(Proxy.id == proxy_id, Proxy.owner_id == user_id)
            ).first()
            
            if not proxy:
                return {"success": False, "message": "Proxy not found"}
            
            # Validate proxy data
            validation = self._validate_proxy_data(proxy_data)
            if not validation["valid"]:
                return {"success": False, "message": validation["message"]}
            
            # Update proxy fields
            proxy.host = proxy_data.host.strip()
            proxy.port = proxy_data.port
            proxy.username = proxy_data.username.strip() if proxy_data.username else ""
            proxy.password = proxy_data.password.strip() if proxy_data.password else ""
            proxy.type = proxy_data.type
            proxy.name = proxy_data.name or f"{proxy_data.host}:{proxy_data.port}"
            
            # Update tags if provided
            if proxy_data.tags is not None:
                proxy.tags.clear()
                for tag_name in proxy_data.tags:
                    tag = db.query(Tag).filter(Tag.name == tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.add(tag)
                        db.flush()
                    proxy.tags.append(tag)
            
            db.commit()
            db.refresh(proxy)
            
            return {"success": True, "data": proxy}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error updating proxy: {str(e)}"}
    
    async def delete_proxies(self, db: Session, user_id: int, proxy_ids: List[int]) -> Dict:
        """Delete multiple proxies"""
        try:
            deleted_count = db.query(Proxy).filter(
                and_(Proxy.id.in_(proxy_ids), Proxy.owner_id == user_id)
            ).delete(synchronize_session=False)
            
            db.commit()
            
            return {
                "success": True,
                "data": {"deleted": deleted_count}
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error deleting proxies: {str(e)}"}
    
    async def test_proxy(self, proxy_data: ProxyTest) -> Dict:
        """Test a single proxy"""
        try:
            start_time = time.time()
            
            # Build proxy URL
            proxy_url = self._build_proxy_url(proxy_data)
            
            # Test with multiple URLs
            for test_url in self.test_urls:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            test_url,
                            proxy=proxy_url,
                            timeout=aiohttp.ClientTimeout(total=15)
                        ) as response:
                            if response.status == 200:
                                response_time = int((time.time() - start_time) * 1000)
                                data = await response.json()
                                
                                # Extract IP from different response formats
                                public_ip = ""
                                if isinstance(data, dict):
                                    public_ip = data.get("origin") or data.get("ip", "")
                                elif isinstance(data, str):
                                    public_ip = data.strip()
                                
                                return {
                                    "success": True,
                                    "status": "live",
                                    "response_time": response_time,
                                    "public_ip": public_ip,
                                    "test_url": test_url,
                                    "message": f"Proxy working ({response_time}ms)"
                                }
                except Exception:
                    continue
            
            return {
                "success": False,
                "status": "dead",
                "message": "Proxy not working"
            }
        except Exception as e:
            return {
                "success": False,
                "status": "dead", 
                "message": f"Test failed: {str(e)}"
            }
    
    async def test_proxies(self, db: Session, user_id: int, proxy_ids: List[int]) -> Dict:
        """Test multiple proxies concurrently"""
        try:
            proxies = db.query(Proxy).filter(
                and_(Proxy.id.in_(proxy_ids), Proxy.owner_id == user_id)
            ).all()
            
            if not proxies:
                return {"success": False, "message": "No proxies found"}
            
            # Test proxies concurrently with semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(5)
            
            async def test_single_proxy(proxy):
                async with semaphore:
                    proxy_test = ProxyTest(
                        host=proxy.host,
                        port=proxy.port,
                        username=proxy.username,
                        password=proxy.password,
                        type=proxy.type
                    )
                    result = await self.test_proxy(proxy_test)
                    
                    # Update proxy in database
                    proxy.status = result["status"]
                    proxy.last_tested = datetime.utcnow()
                    if result["success"]:
                        proxy.response_time = result.get("response_time")
                        proxy.public_ip = result.get("public_ip")
                        proxy.fail_count = 0
                    else:
                        proxy.fail_count = (proxy.fail_count or 0) + 1
                    
                    return {
                        "id": proxy.id,
                        "host": proxy.host,
                        "port": proxy.port,
                        **result
                    }
            
            # Run tests concurrently
            results = await asyncio.gather(*[test_single_proxy(proxy) for proxy in proxies])
            
            # Commit all updates
            db.commit()
            
            live_count = sum(1 for r in results if r["success"])
            dead_count = len(results) - live_count
            
            return {
                "success": True,
                "data": {
                    "results": results,
                    "summary": {
                        "total": len(results),
                        "live": live_count,
                        "dead": dead_count
                    }
                }
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Error testing proxies: {str(e)}"}
    
    async def import_proxies(self, db: Session, user_id: int, proxy_text: str, tags: List[str] = None) -> Dict:
        """Import proxies from text"""
        try:
            if tags is None:
                tags = ["Default"]
            
            lines = [line.strip() for line in proxy_text.split('\n') if line.strip()]
            imported = []
            errors = []
            
            for line in lines:
                try:
                    proxy_data = self._parse_proxy_line(line)
                    if proxy_data:
                        proxy_create = ProxyCreate(**proxy_data, tags=tags)
                        result = await self.add_proxy(db, user_id, proxy_create)
                        if result["success"]:
                            imported.append(result["data"])
                        else:
                            errors.append(f"{line}: {result['message']}")
                    else:
                        errors.append(f"{line}: Invalid format")
                except Exception as e:
                    errors.append(f"{line}: {str(e)}")
            
            return {
                "success": True,
                "data": {
                    "imported": len(imported),
                    "errors": len(errors),
                    "error_details": errors,
                    "proxies": imported
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Error importing proxies: {str(e)}"}
    
    async def get_proxy_stats(self, db: Session, user_id: int) -> Dict:
        """Get proxy statistics"""
        try:
            proxies = db.query(Proxy).filter(Proxy.owner_id == user_id).all()
            
            stats = {
                "total": len(proxies),
                "live": len([p for p in proxies if p.status == "live"]),
                "dead": len([p for p in proxies if p.status == "dead"]),
                "pending": len([p for p in proxies if p.status == "pending"]),
                "by_type": {},
                "by_tag": {},
                "avg_response_time": 0,
                "last_tested": None
            }
            
            # Count by type
            for proxy in proxies:
                proxy_type = proxy.type or "http"
                stats["by_type"][proxy_type] = stats["by_type"].get(proxy_type, 0) + 1
            
            # Count by tag
            for proxy in proxies:
                for tag in proxy.tags:
                    stats["by_tag"][tag.name] = stats["by_tag"].get(tag.name, 0) + 1
            
            # Calculate average response time
            live_proxies = [p for p in proxies if p.status == "live" and p.response_time]
            if live_proxies:
                stats["avg_response_time"] = sum(p.response_time for p in live_proxies) / len(live_proxies)
            
            # Find last tested time
            tested_proxies = [p for p in proxies if p.last_tested]
            if tested_proxies:
                stats["last_tested"] = max(p.last_tested for p in tested_proxies)
            
            return {"success": True, "data": stats}
        except Exception as e:
            return {"success": False, "message": f"Error getting stats: {str(e)}"}
    
    def _validate_proxy_data(self, proxy_data) -> Dict:
        """Validate proxy data"""
        if not proxy_data.host or not proxy_data.port:
            return {"valid": False, "message": "Host and port are required"}
        
        if not re.match(r'^[\w\.-]+$', proxy_data.host):
            return {"valid": False, "message": "Invalid host format"}
        
        if not (1 <= proxy_data.port <= 65535):
            return {"valid": False, "message": "Port must be between 1-65535"}
        
        valid_types = ["http", "https", "socks4", "socks5"]
        if proxy_data.type and proxy_data.type not in valid_types:
            return {"valid": False, "message": "Invalid proxy type"}
        
        return {"valid": True}
    
    def _build_proxy_url(self, proxy_data: ProxyTest) -> str:
        """Build proxy URL for testing"""
        auth = ""
        if proxy_data.username and proxy_data.password:
            auth = f"{proxy_data.username}:{proxy_data.password}@"
        
        return f"{proxy_data.type}://{auth}{proxy_data.host}:{proxy_data.port}"
    
    def _parse_proxy_line(self, line: str) -> Optional[Dict]:
        """Parse proxy line into components"""
        # Remove protocol prefix if exists
        clean_line = line
        protocol_match = re.match(r'^(https?|socks[45]?):\/\/', line, re.IGNORECASE)
        detected_type = "http"
        
        if protocol_match:
            detected_type = protocol_match.group(1).lower()
            if detected_type == "socks":
                detected_type = "socks5"
            clean_line = line[len(protocol_match.group(0)):]
        
        # Format: username:password@host:port
        if "@" in clean_line:
            auth, host_port = clean_line.split("@", 1)
            username, password = auth.split(":", 1) if ":" in auth else (auth, "")
            parts = host_port.split(":")
            if len(parts) >= 2:
                host, port = parts[0], parts[1]
                name = f"{host}:{port}"
                return {
                    "host": host,
                    "port": int(port),
                    "username": username,
                    "password": password,
                    "type": detected_type,
                    "name": name
                }
        else:
            # Format: host:port:username:password or host:port
            parts = clean_line.split(":")
            if len(parts) >= 2:
                host, port = parts[0], parts[1]
                username = parts[2] if len(parts) > 2 else ""
                password = parts[3] if len(parts) > 3 else ""
                name = f"{host}:{port}"
                return {
                    "host": host,
                    "port": int(port),
                    "username": username,
                    "password": password,
                    "type": detected_type,
                    "name": name
                }
        
        return None