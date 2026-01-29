import os
import requests
import jwt
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class JWTAuthManager:
    """
    Manages JWT token authentication for external BSK server API.
    Handles login, token caching, and auto-refresh on expiry.
    """
    
    def __init__(self):
        self.login_url = os.getenv('EXTERNAL_LOGIN_URL', 'https://bsk-server.gov.in/api/auth/login')
        self.username = os.getenv('JWT_USERNAME', 'StateCouncil')
        self.password = os.getenv('JWT_PASSWORD', 'Council@2531')
        self.token = None
        self.token_expiry = None
    
    def get_token(self) -> str:
        """
        Get valid JWT token. Returns cached token if still valid,
        otherwise performs login to get new token.
        
        Returns:
            str: Valid JWT token
        """
        # Check if cached token is still valid
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            logger.debug("Using cached JWT token")
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
            response = requests.post(self.login_url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract token (handle different response formats)
            self.token = data.get('token') or data.get('access_token') or data.get('jwt')
            
            if not self.token:
                raise ValueError("No token found in login response")
            
            # Decode token to get expiry (optional, for caching)
            self._parse_token_expiry()
            
            logger.info(f"✓ Successfully obtained JWT token (expires: {self.token_expiry})")
            return self.token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Login failed: {e}")
            raise
    
    def _parse_token_expiry(self):
        """Parse JWT token to extract expiry time"""
        try:
            # Decode without verification to read claims
            decoded = jwt.decode(self.token, options={"verify_signature": False})
            exp_timestamp = decoded.get('exp')
            
            if exp_timestamp:
                self.token_expiry = datetime.fromtimestamp(exp_timestamp)
                logger.debug(f"Token expires at: {self.token_expiry}")
            else:
                # Default 1 hour expiry if not in token
                self.token_expiry = datetime.now() + timedelta(hours=1)
                logger.debug("Token expiry not found, using 1 hour default")
                
        except Exception as e:
            # If decode fails, use safe default
            logger.warning(f"Could not decode token expiry: {e}")
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


# Global singleton instance
jwt_manager = JWTAuthManager()
