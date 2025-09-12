"""Authentication service for multi-user support."""

import os
from typing import Any

from litai.utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service for handling authentication and user identification."""
    
    def __init__(self):
        """Initialize auth service based on environment."""
        self.mode = "supabase" if os.getenv("SUPABASE_URL") else "local"
        
        if self.mode == "supabase":
            self._init_jwt()
    
    def _init_jwt(self) -> None:
        """Initialize JWT verification for Supabase."""
        self.jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if not self.jwt_secret:
            logger.warning("SUPABASE_JWT_SECRET not set, JWT verification will fail")
    
    def get_user_id(self, auth_header: str | None = None) -> str:
        """Extract user_id from authentication context.
        
        Args:
            auth_header: Optional Authorization header value (e.g., "Bearer <token>")
            
        Returns:
            User ID string - either from JWT or 'local' for dev mode
        """
        if self.mode == "local":
            return "local"
        
        if not auth_header:
            logger.warning("No auth header provided in production mode")
            raise ValueError("Authentication required")
        
        # Extract token from "Bearer <token>" format
        token = auth_header.replace("Bearer ", "").strip()
        if not token:
            logger.warning("Empty token in auth header")
            raise ValueError("Invalid authentication token")
        
        try:
            user_id = self._verify_jwt(token)
            logger.debug("User authenticated", user_id=user_id)
            return user_id
        except Exception as e:
            logger.error("JWT verification failed", error=str(e))
            raise ValueError("Invalid authentication token") from e
    
    def _verify_jwt(self, token: str) -> str:
        """Verify JWT token and extract user_id.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID from the token
            
        Raises:
            ValueError: If token is invalid
        """
        try:
            import jwt
        except ImportError:
            logger.error("PyJWT not installed")
            raise ValueError("JWT support not available")
        
        if not self.jwt_secret:
            raise ValueError("JWT secret not configured")
        
        try:
            # Decode the JWT token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                audience="authenticated"
            )
            
            # Extract user_id from the 'sub' claim
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("No user_id in token")
            
            return user_id
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    def create_jwt_for_testing(self, user_id: str) -> str:
        """Create a JWT token for testing purposes.
        
        Args:
            user_id: User ID to encode in the token
            
        Returns:
            JWT token string
            
        Note:
            This is only for testing and should not be used in production
        """
        if self.mode == "local":
            logger.warning("JWT creation not needed in local mode")
            return ""
        
        try:
            import jwt
            from datetime import datetime, timedelta
        except ImportError:
            logger.error("PyJWT not installed")
            return ""
        
        if not self.jwt_secret:
            logger.error("JWT secret not configured")
            return ""
        
        # Create a token that expires in 1 hour
        payload = {
            "sub": user_id,
            "aud": "authenticated",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token
    
    def validate_api_key(self, api_key: str | None) -> bool:
        """Validate an API key format.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not api_key:
            return False
        
        # Basic validation - OpenAI API keys start with 'sk-'
        if not api_key.startswith("sk-"):
            logger.warning("Invalid API key format")
            return False
        
        # Check minimum length
        if len(api_key) < 20:
            logger.warning("API key too short")
            return False
        
        return True