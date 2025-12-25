import aiohttp
import asyncio
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class OriginalServerService:
    def __init__(self):
        self.base_url = "https://dev.pmbackend.site"
        self.timeout = aiohttp.ClientTimeout(total=15)
        
    async def authenticate_user(self, email: str, password: str, hwid: Optional[str] = None) -> Dict:
        """Authenticate user with original server"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "email": email,
                    "password": password
                }
                if hwid:
                    payload["hwid"] = hwid
                
                async with session.post(
                    f"{self.base_url}/login",
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    result = await response.json()
                    
                    return {
                        "success": response.status == 200 and result.get("success", False),
                        "status_code": response.status,
                        "data": result,
                        "offline": response.status >= 500
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error connecting to original server: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": "Server không khả dụng"},
                "offline": True
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": f"Lỗi kết nối: {str(e)}"},
                "offline": True
            }
    
    async def register_user(self, email: str, password: str) -> Dict:
        """Register user with original server"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "email": email,
                    "password": password
                }
                
                async with session.post(
                    f"{self.base_url}/register",
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    result = await response.json()
                    
                    return {
                        "success": response.status == 200 and result.get("success", False),
                        "status_code": response.status,
                        "data": result,
                        "offline": response.status >= 500
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error connecting to original server: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": "Server không khả dụng"},
                "offline": True
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": f"Lỗi kết nối: {str(e)}"},
                "offline": True
            }
    
    async def change_password(self, current_password: str, new_password: str, token: Optional[str] = None) -> Dict:
        """Change password on original server"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "current_password": current_password,
                    "password": new_password,
                    "password_confirmation": new_password
                }
                
                headers = {}
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                
                async with session.post(
                    f"{self.base_url}/change-password",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    result = await response.json()
                    
                    return {
                        "success": response.status == 200 and result.get("success", False),
                        "status_code": response.status,
                        "data": result,
                        "offline": response.status >= 500
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error connecting to original server: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": "Server không khả dụng"},
                "offline": True
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": f"Lỗi kết nối: {str(e)}"},
                "offline": True
            }
    
    async def get_user_info(self, token: str) -> Dict:
        """Get user info from original server"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {token}"}
                
                async with session.get(
                    f"{self.base_url}/api/user",
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    result = await response.json()
                    
                    return {
                        "success": response.status == 200 and result.get("success", False),
                        "status_code": response.status,
                        "data": result,
                        "offline": response.status >= 500
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error connecting to original server: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": "Server không khả dụng"},
                "offline": True
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": f"Lỗi kết nối: {str(e)}"},
                "offline": True
            }
    
    async def refresh_token(self, token: str) -> Dict:
        """Refresh token on original server"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {token}"}
                
                async with session.post(
                    f"{self.base_url}/refresh",
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    result = await response.json()
                    
                    return {
                        "success": response.status == 200 and result.get("success", False),
                        "status_code": response.status,
                        "data": result,
                        "offline": response.status >= 500
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error connecting to original server: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": "Server không khả dụng"},
                "offline": True
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": f"Lỗi kết nối: {str(e)}"},
                "offline": True
            }
    
    async def get_plans(self) -> Dict:
        """Get subscription plans from original server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/info/plans",
                    timeout=self.timeout
                ) as response:
                    result = await response.json()
                    
                    return {
                        "success": response.status == 200,
                        "status_code": response.status,
                        "data": result,
                        "offline": response.status >= 500
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error connecting to original server: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": "Server không khả dụng"},
                "offline": True
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": f"Lỗi kết nối: {str(e)}"},
                "offline": True
            }
    
    async def get_system_info(self) -> Dict:
        """Get system info from original server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/info/system",
                    timeout=self.timeout
                ) as response:
                    result = await response.json()
                    
                    return {
                        "success": response.status == 200,
                        "status_code": response.status,
                        "data": result,
                        "offline": response.status >= 500
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error connecting to original server: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": "Server không khả dụng"},
                "offline": True
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "status_code": 0,
                "data": {"message": f"Lỗi kết nối: {str(e)}"},
                "offline": True
            }

# Create singleton instance
original_server = OriginalServerService()