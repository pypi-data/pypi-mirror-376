from __future__ import annotations

import os
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from pydantic import BaseModel, Field, validator
from livekit.agents.types import APIConnectOptions, DEFAULT_API_CONNECT_OPTIONS

logger = logging.getLogger(__name__)

# Valid TTS engines supported by NextEVI
VALID_TTS_ENGINES = {
    "orpheus", "ethos", "kokoro", "chatterbox", "higgs"
}

# Valid LLM providers supported by NextEVI
VALID_LLM_PROVIDERS = {
    "anthropic", "openai", "together", "groq"
}

# Default voice IDs for different TTS engines
DEFAULT_VOICE_IDS = {
    "orpheus": "leo",
    "ethos": "sarah", 
    "kokoro": "ava",
    "chatterbox": "default",
    "higgs": "alex",
}

# NextEVI platform constants
NEXTEVI_BASE_URL = "wss://api.nextevi.com"
NEXTEVI_SAMPLE_RATE = 24000
NEXTEVI_CHANNELS = 1


class NextEVIConfigError(Exception):
    """Configuration validation error"""
    pass


class NextEVIConfig(BaseModel):
    """
    NextEVI Realtime Model Configuration
    
    Provides comprehensive configuration management for NextEVI integration
    with validation, defaults, and environment variable support.
    """
    
    # Required authentication parameters
    api_key: str = Field(..., description="NextEVI API key (must start with 'oak_')")
    config_id: str = Field(..., description="NextEVI configuration ID")
    project_id: Optional[str] = Field(None, description="NextEVI project ID (optional)")
    
    # Connection settings
    base_url: str = Field(NEXTEVI_BASE_URL, description="NextEVI WebSocket base URL")
    conn_options: APIConnectOptions = Field(
        default_factory=lambda: DEFAULT_API_CONNECT_OPTIONS,
        description="API connection options"
    )
    
    # TTS Configuration
    tts_engine: str = Field("orpheus", description="TTS engine selection")
    voice_id: str = Field("", description="Voice ID for TTS (auto-selected if empty)")
    speech_speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech rate multiplier")
    
    # LLM Configuration
    llm_provider: str = Field("anthropic", description="LLM provider")
    temperature: float = Field(0.8, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens per response")
    
    # Advanced Features
    enable_emotion_analysis: bool = Field(True, description="Enable emotion analysis")
    enable_knowledge_base: bool = Field(True, description="Enable knowledge base integration")
    enable_interruption: bool = Field(True, description="Enable voice interruption")
    recording_enabled: bool = Field(False, description="Enable session recording")
    
    # Audio settings
    sample_rate: int = Field(NEXTEVI_SAMPLE_RATE, description="Audio sample rate")
    channels: int = Field(NEXTEVI_CHANNELS, description="Audio channels")
    
    # Session settings
    session_timeout: float = Field(1800.0, ge=60.0, description="Session timeout in seconds")
    keepalive_interval: float = Field(30.0, ge=5.0, description="Keepalive interval in seconds")
    
    # Debugging and monitoring
    debug_mode: bool = Field(False, description="Enable debug logging")
    log_audio_events: bool = Field(False, description="Log audio processing events")
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        extra = "forbid"  # Don't allow extra fields
        
    @validator('api_key')
    def validate_api_key(cls, v: str) -> str:
        """Validate NextEVI API key format"""
        if not v:
            raise NextEVIConfigError("API key is required")
        if not v.startswith('oak_'):
            raise NextEVIConfigError("NextEVI API key must start with 'oak_'")
        if len(v) < 10:  # Minimum reasonable length
            raise NextEVIConfigError("API key appears to be too short")
        return v
    
    @validator('config_id')
    def validate_config_id(cls, v: str) -> str:
        """Validate configuration ID"""
        if not v:
            raise NextEVIConfigError("Configuration ID is required")
        if len(v) < 8:  # Minimum reasonable length
            raise NextEVIConfigError("Configuration ID appears to be too short")
        return v
    
    @validator('base_url')
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL format"""
        if not v:
            raise NextEVIConfigError("Base URL is required")
        if not (v.startswith('wss://') or v.startswith('ws://')):
            # Auto-add wss:// if missing
            v = f"wss://{v}"
        return v
    
    @validator('tts_engine')
    def validate_tts_engine(cls, v: str) -> str:
        """Validate TTS engine selection"""
        if v not in VALID_TTS_ENGINES:
            raise NextEVIConfigError(
                f"Invalid TTS engine '{v}'. Valid options: {', '.join(VALID_TTS_ENGINES)}"
            )
        return v
    
    @validator('llm_provider') 
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider selection"""
        if v not in VALID_LLM_PROVIDERS:
            raise NextEVIConfigError(
                f"Invalid LLM provider '{v}'. Valid options: {', '.join(VALID_LLM_PROVIDERS)}"
            )
        return v
    
    @validator('voice_id')
    def validate_voice_id(cls, v: str, values: Dict[str, Any]) -> str:
        """Auto-select voice ID if not provided"""
        if not v and 'tts_engine' in values:
            engine = values['tts_engine']
            v = DEFAULT_VOICE_IDS.get(engine, "default")
            logger.info(f"Auto-selected voice ID '{v}' for TTS engine '{engine}'")
        return v
    
    @validator('sample_rate')
    def validate_sample_rate(cls, v: int) -> int:
        """Validate audio sample rate"""
        valid_rates = {8000, 16000, 22050, 24000, 44100, 48000}
        if v not in valid_rates:
            raise NextEVIConfigError(
                f"Invalid sample rate {v}. Valid options: {', '.join(map(str, valid_rates))}"
            )
        return v
    
    @validator('channels')
    def validate_channels(cls, v: int) -> int:
        """Validate audio channels"""
        if v not in {1, 2}:
            raise NextEVIConfigError("Only mono (1) and stereo (2) channels are supported")
        return v
    
    @classmethod
    def from_env(cls, prefix: str = "NEXTEVI_") -> NextEVIConfig:
        """
        Create configuration from environment variables
        
        Args:
            prefix: Environment variable prefix (default: "NEXTEVI_")
            
        Returns:
            NextEVIConfig instance
        """
        env_vars = {}
        
        # Map environment variables to config fields
        env_mappings = {
            f"{prefix}API_KEY": "api_key",
            f"{prefix}CONFIG_ID": "config_id", 
            f"{prefix}PROJECT_ID": "project_id",
            f"{prefix}BASE_URL": "base_url",
            f"{prefix}WEBSOCKET_URL": "base_url",  # Alternative name
            f"{prefix}TTS_ENGINE": "tts_engine",
            f"{prefix}VOICE_ID": "voice_id",
            f"{prefix}SPEECH_SPEED": "speech_speed",
            f"{prefix}LLM_PROVIDER": "llm_provider",
            f"{prefix}TEMPERATURE": "temperature",
            f"{prefix}MAX_TOKENS": "max_tokens",
            f"{prefix}ENABLE_EMOTION": "enable_emotion_analysis",
            f"{prefix}ENABLE_KNOWLEDGE": "enable_knowledge_base",
            f"{prefix}ENABLE_INTERRUPTION": "enable_interruption",
            f"{prefix}RECORDING_ENABLED": "recording_enabled",
            f"{prefix}DEBUG_MODE": "debug_mode",
        }
        
        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # Convert string values to appropriate types
                if config_key in {"speech_speed", "temperature"}:
                    env_vars[config_key] = float(env_value)
                elif config_key in {"max_tokens"}:
                    env_vars[config_key] = int(env_value) if env_value else None
                elif config_key in {"enable_emotion_analysis", "enable_knowledge_base", 
                                    "enable_interruption", "recording_enabled", "debug_mode"}:
                    env_vars[config_key] = env_value.lower() in {"true", "1", "yes", "on"}
                else:
                    env_vars[config_key] = env_value
        
        logger.info(f"Loaded {len(env_vars)} configuration values from environment")
        return cls(**env_vars)
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> NextEVIConfig:
        """
        Create configuration from JSON file
        
        Args:
            config_path: Path to JSON configuration file
            
        Returns:
            NextEVIConfig instance
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise NextEVIConfigError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            logger.info(f"Loaded configuration from file: {config_path}")
            return cls(**config_data)
            
        except json.JSONDecodeError as e:
            raise NextEVIConfigError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise NextEVIConfigError(f"Failed to load configuration file: {e}")
    
    @classmethod 
    def from_dict(cls, config_dict: Dict[str, Any]) -> NextEVIConfig:
        """
        Create configuration from dictionary
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            NextEVIConfig instance
        """
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary
        
        Returns:
            Configuration dictionary
        """
        return self.dict()
    
    def to_file(self, config_path: Union[str, Path]) -> None:
        """
        Save configuration to JSON file
        
        Args:
            config_path: Path to save configuration file
        """
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and handle non-serializable types
        config_data = self.dict()
        
        # Remove non-serializable fields
        config_data.pop('conn_options', None)
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Saved configuration to file: {config_path}")
            
        except Exception as e:
            raise NextEVIConfigError(f"Failed to save configuration file: {e}")
    
    def get_websocket_url(self, connection_id: Optional[str] = None) -> str:
        """
        Build the complete WebSocket URL with sessionId and query parameters (matching React demo exactly)
        
        Args:
            connection_id: Optional connection ID for the WebSocket path
            
        Returns:
            Complete WebSocket URL
        """
        # Generate session ID in React demo format if not provided
        if not connection_id:
            import time
            import random
            import string
            # Match React demo format exactly: voice_{timestamp}_{random9chars}
            # React demo: `voice_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
            timestamp = int(time.time() * 1000)
            # Generate 9-character random string like JavaScript Math.random().toString(36).substr(2, 9)
            random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
            connection_id = f"voice_{timestamp}_{random_chars}"
        
        base_url = self.base_url
        if base_url.endswith('/'):
            base_url = base_url.rstrip('/')
        
        # Build the URL matching React demo format exactly: wss://api.nextevi.com/ws/voice/{sessionId}
        # React demo BASE_WEBSOCKET_URL: "wss://api.nextevi.com/ws/voice/"
        # React demo URL: `${this.BASE_WEBSOCKET_URL}${sessionId}?api_key=...`
        ws_url = f"{base_url}/ws/voice/{connection_id}"
        
        # Build query parameters
        params = {
            'api_key': self.api_key,
            'config_id': self.config_id,
        }
        
        if self.project_id:
            params['project_id'] = self.project_id
        
        # Build query string
        query_parts = [f"{k}={v}" for k, v in params.items()]
        query_string = "&".join(query_parts)
        
        return f"{ws_url}?{query_string}"
    
    def get_connection_headers(self) -> Dict[str, str]:
        """
        Build headers for WebSocket connection
        
        Note: Authentication is handled via query parameters, not headers.
        Only include non-authentication headers here.
        
        Returns:
            Connection headers dictionary
        """
        return {
            'User-Agent': 'livekit-nextevi/0.1.0',
            # Authentication via query parameters, not headers
        }
    
    def validate_connection_requirements(self) -> bool:
        """
        Validate that all required connection parameters are present
        
        Returns:
            True if all requirements are met
            
        Raises:
            NextEVIConfigError: If validation fails
        """
        if not self.api_key:
            raise NextEVIConfigError("API key is required for connection")
        if not self.config_id:
            raise NextEVIConfigError("Configuration ID is required for connection")
        if not self.base_url:
            raise NextEVIConfigError("Base URL is required for connection")
        
        return True
    
    def get_session_metadata(self) -> Dict[str, Any]:
        """
        Get session metadata for logging and monitoring
        
        Returns:
            Session metadata dictionary
        """
        return {
            'config_id': self.config_id,
            'project_id': self.project_id,
            'tts_engine': self.tts_engine,
            'voice_id': self.voice_id,
            'llm_provider': self.llm_provider,
            'features': {
                'emotion_analysis': self.enable_emotion_analysis,
                'knowledge_base': self.enable_knowledge_base,
                'interruption': self.enable_interruption,
                'recording': self.recording_enabled,
            },
            'audio': {
                'sample_rate': self.sample_rate,
                'channels': self.channels,
            }
        }
    
    def __str__(self) -> str:
        """String representation (sanitized for logging)"""
        return (
            f"NextEVIConfig("
            f"api_key=oak_*****, "
            f"config_id={self.config_id}, "
            f"project_id={self.project_id}, "
            f"tts_engine={self.tts_engine}, "
            f"voice_id={self.voice_id})"
        )


# Configuration factory functions
def create_config(
    api_key: str,
    config_id: str,
    project_id: Optional[str] = None,
    **kwargs
) -> NextEVIConfig:
    """
    Create NextEVI configuration with validation
    
    Args:
        api_key: NextEVI API key
        config_id: NextEVI configuration ID
        project_id: NextEVI project ID (optional)
        **kwargs: Additional configuration parameters
        
    Returns:
        NextEVIConfig instance
    """
    config_data = {
        'api_key': api_key,
        'config_id': config_id,
        'project_id': project_id,
        **kwargs
    }
    
    return NextEVIConfig(**config_data)


def load_config(
    config_source: Optional[Union[str, Path, Dict[str, Any]]] = None,
    env_prefix: str = "NEXTEVI_"
) -> NextEVIConfig:
    """
    Load NextEVI configuration from various sources
    
    Args:
        config_source: Configuration source (file path, dict, or None for env)
        env_prefix: Environment variable prefix for env loading
        
    Returns:
        NextEVIConfig instance
    """
    if config_source is None:
        # Load from environment
        return NextEVIConfig.from_env(env_prefix)
    elif isinstance(config_source, dict):
        # Load from dictionary
        return NextEVIConfig.from_dict(config_source)
    else:
        # Load from file
        return NextEVIConfig.from_file(config_source)


# Export for convenience
__all__ = [
    'NextEVIConfig',
    'NextEVIConfigError',
    'create_config',
    'load_config',
    'VALID_TTS_ENGINES',
    'VALID_LLM_PROVIDERS',
    'DEFAULT_VOICE_IDS',
]