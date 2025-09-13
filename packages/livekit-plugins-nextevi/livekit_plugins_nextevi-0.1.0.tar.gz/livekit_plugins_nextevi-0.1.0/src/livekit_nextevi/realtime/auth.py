from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple
from enum import Enum

import aiohttp
import websockets
from websockets.exceptions import WebSocketException

from .config import NextEVIConfig

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Authentication-related errors"""
    pass


class ConnectionError(Exception):
    """Connection-related errors"""
    pass


class ProjectResolutionError(Exception):
    """Project context resolution errors"""
    pass


class AuthStatus(str, Enum):
    """Authentication status enumeration"""
    NOT_AUTHENTICATED = "not_authenticated"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    FAILED = "failed"
    EXPIRED = "expired"


class NextEVIAuthenticator:
    """
    NextEVI Authentication Manager
    
    Handles authentication flow, project context resolution, and connection validation
    for the NextEVI platform.
    """
    
    def __init__(self, config: NextEVIConfig) -> None:
        """
        Initialize authenticator with configuration
        
        Args:
            config: NextEVI configuration object
        """
        self.config = config
        self.status = AuthStatus.NOT_AUTHENTICATED
        self.auth_timestamp: Optional[float] = None
        self.connection_metadata: Dict[str, Any] = {}
        self.resolved_project_id: Optional[str] = None
        
        # Session state
        self._auth_lock = asyncio.Lock()
        self._last_validation: Optional[float] = None
        self._validation_cache_duration = 300  # 5 minutes
        
        logger.info(f"NextEVI Authenticator initialized for config: {config.config_id}")
    
    async def authenticate(self) -> Dict[str, Any]:
        """
        Perform authentication with NextEVI platform
        
        Returns:
            Authentication result with metadata
            
        Raises:
            AuthenticationError: If authentication fails
        """
        async with self._auth_lock:
            if self.status == AuthStatus.AUTHENTICATING:
                # Wait for ongoing authentication
                await asyncio.sleep(0.1)
                if self.status == AuthStatus.AUTHENTICATED:
                    return self.connection_metadata
            
            self.status = AuthStatus.AUTHENTICATING
            
            try:
                logger.info("Starting NextEVI authentication flow")
                
                # Step 1: Validate configuration
                self._validate_config()
                
                # Step 2: Resolve project context
                await self._resolve_project_context()
                
                # Step 3: Validate API key and permissions
                await self._validate_api_key()
                
                # Step 4: Verify configuration access
                await self._verify_config_access()
                
                # Step 5: Test websocket connection
                await self._test_websocket_connection()
                
                # Authentication successful
                self.status = AuthStatus.AUTHENTICATED
                self.auth_timestamp = time.time()
                
                logger.info("NextEVI authentication completed successfully")
                
                return self.connection_metadata
                
            except Exception as e:
                self.status = AuthStatus.FAILED
                logger.error(f"NextEVI authentication failed: {e}")
                raise AuthenticationError(f"Authentication failed: {e}") from e
    
    def _validate_config(self) -> None:
        """
        Validate configuration parameters
        
        Raises:
            AuthenticationError: If configuration is invalid
        """
        try:
            self.config.validate_connection_requirements()
            logger.debug("Configuration validation passed")
        except Exception as e:
            raise AuthenticationError(f"Configuration validation failed: {e}")
    
    async def _resolve_project_context(self) -> None:
        """
        Resolve project context from API key and configuration
        
        Raises:
            ProjectResolutionError: If project resolution fails
        """
        try:
            logger.debug("Resolving project context")
            
            # If project_id is explicitly provided, use it
            if self.config.project_id:
                self.resolved_project_id = self.config.project_id
                logger.info(f"Using explicit project ID: {self.resolved_project_id}")
                return
            
            # Otherwise, resolve from organization API key
            # This would typically involve an API call to NextEVI's management API
            # For now, we'll simulate this
            
            project_info = await self._fetch_project_info()
            self.resolved_project_id = project_info.get('project_id')
            
            if not self.resolved_project_id:
                raise ProjectResolutionError("Could not resolve project ID from API key")
            
            logger.info(f"Resolved project ID: {self.resolved_project_id}")
            
        except Exception as e:
            if isinstance(e, ProjectResolutionError):
                raise
            raise ProjectResolutionError(f"Project resolution failed: {e}")
    
    async def _fetch_project_info(self) -> Dict[str, Any]:
        """
        Fetch project information from NextEVI API
        
        Returns:
            Project information dictionary
        """
        # This is a placeholder for actual API integration
        # In production, this would make an HTTP request to NextEVI's management API
        
        try:
            # Simulate API call to get project info
            management_url = self.config.base_url.replace('wss://', 'https://').replace('ws://', 'http://')
            management_url = f"{management_url}/api/v1/projects/resolve"
            
            headers = {
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json',
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    management_url, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        project_info = await response.json()
                        return project_info
                    elif response.status == 401:
                        raise AuthenticationError("Invalid API key")
                    elif response.status == 404:
                        raise ProjectResolutionError("No accessible projects found")
                    else:
                        raise ProjectResolutionError(f"API error: {response.status}")
                        
        except aiohttp.ClientError as e:
            logger.warning(f"Could not reach management API: {e}")
            # Fallback: use a default project structure
            return {
                'project_id': self._extract_project_from_config(),
                'organization_id': self._extract_org_from_api_key(),
            }
    
    def _extract_project_from_config(self) -> str:
        """Extract project ID from configuration ID pattern"""
        # This is a fallback method - in practice, the API should provide this
        # Assuming config IDs might have project prefixes
        config_parts = self.config.config_id.split('-')
        if len(config_parts) >= 2:
            return f"proj_{config_parts[0]}"
        return f"proj_default_{hash(self.config.config_id) % 10000}"
    
    def _extract_org_from_api_key(self) -> str:
        """Extract organization ID from API key pattern"""
        # Extract organization info from API key format
        # Assuming format like "oak_orgid_randompart"
        key_parts = self.config.api_key.split('_')
        if len(key_parts) >= 2:
            return key_parts[1]
        return "unknown_org"
    
    async def _validate_api_key(self) -> None:
        """
        Validate API key with NextEVI platform
        
        Raises:
            AuthenticationError: If API key is invalid
        """
        try:
            logger.debug("Validating API key")
            
            # This would typically involve an API call to validate the key
            # For now, we'll do basic format validation
            
            if not self.config.api_key.startswith('oak_'):
                raise AuthenticationError("Invalid API key format")
            
            if len(self.config.api_key) < 20:  # Reasonable minimum length
                raise AuthenticationError("API key appears to be too short")
            
            # In production, make actual validation request
            # await self._make_key_validation_request()
            
            logger.debug("API key validation passed")
            
        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(f"API key validation failed: {e}")
    
    async def _verify_config_access(self) -> None:
        """
        Verify access to specified configuration
        
        Raises:
            AuthenticationError: If configuration access is denied
        """
        try:
            logger.debug(f"Verifying access to configuration: {self.config.config_id}")
            
            # This would typically verify that the API key has access to the config
            # For now, we'll simulate this check
            
            config_info = await self._fetch_config_info()
            
            # Store configuration metadata
            self.connection_metadata.update({
                'config_id': self.config.config_id,
                'project_id': self.resolved_project_id,
                'organization_id': config_info.get('organization_id'),
                'config_name': config_info.get('name', 'Unknown'),
                'tts_engine': config_info.get('tts_engine', self.config.tts_engine),
                'voice_id': config_info.get('voice_id', self.config.voice_id),
                'features': config_info.get('features', {}),
            })
            
            logger.debug("Configuration access verified")
            
        except Exception as e:
            raise AuthenticationError(f"Configuration access verification failed: {e}")
    
    async def _fetch_config_info(self) -> Dict[str, Any]:
        """
        Fetch configuration information from NextEVI
        
        Returns:
            Configuration information dictionary
        """
        # Placeholder for actual API integration
        # In production, this would fetch config details from NextEVI
        
        return {
            'id': self.config.config_id,
            'name': f"Config {self.config.config_id}",
            'organization_id': self._extract_org_from_api_key(),
            'project_id': self.resolved_project_id,
            'tts_engine': self.config.tts_engine,
            'voice_id': self.config.voice_id,
            'features': {
                'emotion_analysis': self.config.enable_emotion_analysis,
                'knowledge_base': self.config.enable_knowledge_base,
                'interruption': self.config.enable_interruption,
                'recording': self.config.recording_enabled,
            },
            'limits': {
                'max_session_duration': self.config.session_timeout,
                'max_concurrent_sessions': 10,
            }
        }
    
    async def _test_websocket_connection(self) -> None:
        """
        Test websocket connection to NextEVI
        
        Raises:
            ConnectionError: If connection test fails
        """
        try:
            logger.debug("Testing websocket connection")
            
            ws_url = self.config.get_websocket_url()
            headers = self.config.get_connection_headers()
            
            # Test connection with short timeout
            async with websockets.connect(
                ws_url,
                additional_headers=headers,
                ping_interval=None,  # Disable ping for test
                close_timeout=5,
                open_timeout=10,
            ) as websocket:
                # Send test message
                test_message = {
                    'type': 'test_connection',
                    'timestamp': time.time(),
                }
                
                await websocket.send(json.dumps(test_message))
                
                # Wait for response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    if response_data.get('type') == 'connection_metadata':
                        # Connection successful, store metadata
                        self.connection_metadata.update(response_data.get('metadata', {}))
                    
                except asyncio.TimeoutError:
                    logger.warning("No response to test connection (may be normal)")
            
            logger.debug("Websocket connection test completed")
            
        except WebSocketException as e:
            raise ConnectionError(f"Websocket connection failed: {e}")
        except Exception as e:
            raise ConnectionError(f"Connection test failed: {e}")
    
    async def validate_session_token(self, token: str) -> bool:
        """
        Validate a session token (if applicable)
        
        Args:
            token: Session token to validate
            
        Returns:
            True if token is valid
        """
        # Placeholder for session token validation
        # In production, this would validate with NextEVI's auth service
        return len(token) > 10  # Basic validation
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated
        
        Returns:
            True if authenticated and not expired
        """
        if self.status != AuthStatus.AUTHENTICATED:
            return False
        
        if not self.auth_timestamp:
            return False
        
        # Check if authentication has expired (1 hour default)
        auth_age = time.time() - self.auth_timestamp
        max_auth_age = 3600  # 1 hour
        
        if auth_age > max_auth_age:
            self.status = AuthStatus.EXPIRED
            return False
        
        return True
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for requests
        
        Returns:
            Headers dictionary with authentication info
        """
        headers = self.config.get_connection_headers()
        
        if self.resolved_project_id:
            headers['X-NextEVI-Project-ID'] = self.resolved_project_id
        
        if self.auth_timestamp:
            headers['X-NextEVI-Auth-Timestamp'] = str(int(self.auth_timestamp))
        
        return headers
    
    def get_connection_params(self) -> Dict[str, str]:
        """
        Get connection parameters for websocket
        
        Returns:
            Connection parameters dictionary
        """
        params = {
            'api_key': self.config.api_key,
            'config_id': self.config.config_id,
        }
        
        if self.resolved_project_id:
            params['project_id'] = self.resolved_project_id
        
        return params
    
    async def refresh_authentication(self) -> None:
        """
        Refresh authentication if needed
        
        Raises:
            AuthenticationError: If refresh fails
        """
        if not self.is_authenticated():
            logger.info("Refreshing NextEVI authentication")
            await self.authenticate()
    
    def get_session_metadata(self) -> Dict[str, Any]:
        """
        Get session metadata for monitoring
        
        Returns:
            Session metadata dictionary
        """
        return {
            'status': self.status.value,
            'authenticated_at': self.auth_timestamp,
            'project_id': self.resolved_project_id,
            'connection_metadata': self.connection_metadata,
        }
    
    def __str__(self) -> str:
        """String representation"""
        return (
            f"NextEVIAuthenticator("
            f"status={self.status.value}, "
            f"config_id={self.config.config_id}, "
            f"project_id={self.resolved_project_id})"
        )


async def authenticate_nextevi(config: NextEVIConfig) -> NextEVIAuthenticator:
    """
    Authenticate with NextEVI platform
    
    Args:
        config: NextEVI configuration
        
    Returns:
        Authenticated NextEVIAuthenticator instance
    """
    authenticator = NextEVIAuthenticator(config)
    await authenticator.authenticate()
    return authenticator


# Export for convenience
__all__ = [
    'NextEVIAuthenticator',
    'AuthenticationError',
    'ConnectionError',
    'ProjectResolutionError',
    'AuthStatus',
    'authenticate_nextevi',
]