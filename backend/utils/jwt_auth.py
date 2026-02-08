import os
import requests
import jwt
import ssl
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Suppress InsecureRequestWarning only if needed (though we use create_default_context which is safer)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LegacyHttpAdapter(HTTPAdapter):
    """
    Custom HTTP adapter to allow legacy SSL/TLS renegotiation.
    Required for servers running older OpenSSL versions (like BSK).
    """
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        # OP_LEGACY_SERVER_CONNECT = 0x4 (Allows connecting to legacy servers)
        ctx.options |= 0x4 
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx)

class JWTAuthManager:
    """
    Manages JWT token authentication for external BSK server API.
    Handles login, token caching, and auto-refresh on expiry.
    """
    
    def __init__(self):
        self.login_url = os.getenv('EXTERNAL_LOGIN_URL', 'https://bsk.wb.gov.in/aiapi/generate_token')
        self.username = os.getenv('JWT_USERNAME', 'admin')
        self.password = os.getenv('JWT_PASSWORD', '123456')
        self.token = None
        self.token_expiry = None
        
        # Initialize session with legacy adapter
        self.session = requests.Session()
        self.session.mount('https://', LegacyHttpAdapter())
    
    def get_token(self) -> str:
        """
        Get valid JWT token. Returns cached token if still valid,
        otherwise performs login to get new token.
        
        Returns:
            str: Valid JWT token
        """
        # Check if cached token is still valid
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            # logger.debug("Using cached JWT token")
            return self.token
        
        # Token expired or not present, get new one
        logger.info("Getting new JWT token...")
        return self.login()
    
    def login(self) -> str:
        """
        Login to external API and get JWT token.
        
        Returns:
            str: Fresh JWT token
            
        Raises:
            requests.exceptions.RequestException: If login fails
        """
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            logger.info(f"Logging in to {self.login_url}...")
            # Use self.session (with legacy adapter) instead of requests
            response = self.session.post(self.login_url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # New Response Format: {"status": 1, "token": "...", "expiresIn": "24h"}
            if data.get("status") != 1:
                raise ValueError(f"Login failed: Status is not 1. Response: {data}")

            self.token = data.get('token')
            
            if not self.token:
                raise ValueError("No token found in login response")
            
            # Parse expiry from response (e.g., "24h")
            expires_in_str = data.get("expiresIn", "24h")
            self._calculate_expiry(expires_in_str)
            
            logger.info(f"✓ Successfully obtained JWT token (expires: {self.token_expiry})")
            return self.token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Login failed: {e}")
            raise
    
    def _calculate_expiry(self, expires_in_str: str):
        """Calculate exact expiry datetime from '24h' format"""
        try:
            # Simple parser for "24h"
            if isinstance(expires_in_str, str) and expires_in_str.endswith('h'):
                hours = int(expires_in_str[:-1])
                self.token_expiry = datetime.now() + timedelta(hours=hours)
            else:
                # Fallback default
                self.token_expiry = datetime.now() + timedelta(hours=1)
                logger.warning(f"Unknown expiry format: {expires_in_str}. Using 1 hour default.")
                
            logger.debug(f"Token expires at: {self.token_expiry}")

        except Exception as e:
            logger.warning(f"Error calculating token expiry: {e}")
            self.token_expiry = datetime.now() + timedelta(hours=1)
    
    def refresh_token(self) -> str:
        """
        Force token refresh by performing new login.
        
        Returns:
            str: Fresh JWT token
        """
        logger.info("Force refreshing JWT token...")
        return self.login()
    
    def get_auth_header(self) -> dict:
        """
        Get authorization header with valid token.
        
        Returns:
            dict: Headers dict with Authorization bearer token
        """
        token = self.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get_session(self) -> requests.Session:
        """Returns the configured session with Legacy SSL Adapter"""
        return self.session


# Global singleton instance
jwt_manager = JWTAuthManager()
