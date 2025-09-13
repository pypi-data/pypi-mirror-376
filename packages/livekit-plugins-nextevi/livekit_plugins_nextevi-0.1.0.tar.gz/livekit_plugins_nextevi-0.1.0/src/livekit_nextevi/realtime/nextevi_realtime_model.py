from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
import weakref
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Literal, Optional, Union, cast, overload

import aiohttp
import websockets
import numpy as np
from pydantic import BaseModel

from livekit import rtc
from livekit.agents import APIConnectionError, APIError, io, llm, utils
from livekit.agents.types import (
    DEFAULT_API_CONNECT_OPTIONS,
    NOT_GIVEN,
    APIConnectOptions,
    NotGivenOr,
)

from .nextevi_websocket_client import NextEVIWebSocketClient
from .config import NextEVIConfig

logger = logging.getLogger(__name__)

# NextEVI audio format constants
NEXTEVI_SAMPLE_RATE = 24000
NEXTEVI_NUM_CHANNELS = 1
NEXTEVI_BASE_URL = "wss://api.nextevi.com"

# Default configuration values for NextEVI
DEFAULT_TTS_ENGINE = "orpheus"
DEFAULT_VOICE_ID = "leo"
DEFAULT_LLM_PROVIDER = "anthropic"




class NextEVIRealtimeModel(llm.RealtimeModel):
    """
    NextEVI Realtime Model for LiveKit agents.
    
    Provides a drop-in replacement for OpenAI Realtime API using NextEVI's
    voice AI platform with real-time speech-to-speech capabilities.
    """
    
    def __init__(
        self,
        *,
        api_key: str = None,
        config_id: str = None,
        project_id: Optional[str] = None,
        base_url: str = NEXTEVI_BASE_URL,
        tts_engine: str = DEFAULT_TTS_ENGINE,
        voice_id: str = DEFAULT_VOICE_ID,
        llm_provider: str = DEFAULT_LLM_PROVIDER,
        temperature: float = 0.8,
        speech_speed: float = 1.0,
        enable_emotion_analysis: bool = True,
        enable_knowledge_base: bool = True,
        enable_interruption: bool = True,
        recording_enabled: bool = False,
        http_session: aiohttp.ClientSession | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        config: NextEVIConfig = None,
    ) -> None:
        """
        Initialize NextEVI Realtime Model
        
        Args:
            api_key: NextEVI API key (starts with 'oak_')
            config_id: NextEVI configuration ID
            project_id: Optional NextEVI project ID
            base_url: NextEVI websocket base URL
            tts_engine: TTS engine (orpheus, ethos, kokoro, etc.)
            voice_id: Voice ID for TTS
            llm_provider: LLM provider (anthropic, openai, etc.)
            temperature: LLM temperature
            speech_speed: TTS speed multiplier
            enable_emotion_analysis: Enable emotion analysis
            enable_knowledge_base: Enable knowledge base integration
            enable_interruption: Enable voice interruption
            recording_enabled: Enable session recording
            http_session: Optional aiohttp session
            conn_options: API connection options
            config: Optional pre-built configuration object
        """
        # Define NextEVI capabilities
        capabilities = llm.RealtimeCapabilities(
            message_truncation=True,      # NextEVI can handle message truncation
            turn_detection=True,          # NextEVI has built-in VAD for turn detection
            user_transcription=True,      # NextEVI provides user speech transcription
            auto_tool_reply_generation=True,  # NextEVI can generate automatic tool replies
            audio_output=True,            # NextEVI provides audio output
        )
        
        super().__init__(capabilities=capabilities)
        
        # Use provided config or create new one
        if config:
            self._config = config
        else:
            # Validate required parameters
            if not api_key:
                raise ValueError("NextEVI API key is required")
            if not api_key.startswith('oak_'):
                raise ValueError("NextEVI API key must start with 'oak_'")
            if not config_id:
                raise ValueError("NextEVI config_id is required")
            
            # Store configuration
            self._config = NextEVIConfig(
                api_key=api_key,
                config_id=config_id,
                project_id=project_id,
                base_url=base_url,
                tts_engine=tts_engine,
                voice_id=voice_id,
                speech_speed=speech_speed,
                llm_provider=llm_provider,
                temperature=temperature,
                enable_emotion_analysis=enable_emotion_analysis,
                enable_knowledge_base=enable_knowledge_base,
                enable_interruption=enable_interruption,
                recording_enabled=recording_enabled,
                conn_options=conn_options,
            )
        
        # Initialize components (moved complexity from agent code)
        self._http_session = http_session
        self._own_http_session = http_session is None
        self._websocket_client: Optional[NextEVIWebSocketClient] = None
        
        # Audio processing (moved from agent code)
        self._audio_input_ch = utils.aio.Chan[rtc.AudioFrame]()
        self._audio_output_ch = utils.aio.Chan[rtc.AudioFrame]()
        
        
        # LiveKit integration state
        self._connected = False
        
        # TTS state tracking for interruptions (like React demo)
        self._is_tts_playing = False
        self._audio_source = None  # Reference to LiveKit AudioSource for interruption control
        self._livekit_ctx = None  # Reference to LiveKit context for disconnection signaling
        self._transcription_callback = None  # Callback for playground transcription forwarding
        
        logger.info(f"NextEVI Realtime Model initialized with config_id: {config_id}")

    @property
    def config(self) -> NextEVIConfig:
        """Get the NextEVI configuration"""
        return self._config
    
    
    async def aclose(self) -> None:
        """Close the realtime model and cleanup resources"""
        if self._websocket_client:
            await self._websocket_client.disconnect()
        
        if self._own_http_session and self._http_session:
            await self._http_session.close()
            
        # Close audio channels
        self._audio_input_ch.close()
        self._audio_output_ch.close()
        
        logger.info("NextEVI Realtime Model closed")
    
    # OpenAI-like methods (moved from agent code)
    async def push_audio(self, audio_frame: rtc.AudioFrame) -> None:
        """
        Push audio frame to NextEVI for processing (like OpenAI's push_audio)
        This hides all the complexity that was in the agent code.
        """
        if not self._connected:
            await self._ensure_connection()
        
        if self._websocket_client:
            await self._websocket_client.send_audio(audio_frame)
        
        # Also add to input channel for session tracking
        self._audio_input_ch.send_nowait(audio_frame)
    
    
    async def commit_audio(self) -> None:
        """
        Commit pending audio input (like OpenAI's commit_audio)
        This is a no-op for NextEVI as audio is streamed in real-time.
        """
        # NextEVI processes audio in real-time, so this is a no-op
        pass
    
    def audio_output_stream(self) -> utils.aio.Chan[rtc.AudioFrame]:
        """
        Get stream of audio output from NextEVI (like OpenAI's audio stream)
        This hides the complexity of TTS chunk handling.
        """
        return self._audio_output_ch
    
    def set_audio_source(self, audio_source) -> None:
        """Set LiveKit AudioSource reference for interruption control"""
        self._audio_source = audio_source
    
    def set_livekit_context(self, ctx) -> None:
        """Set LiveKit context reference for disconnection signaling"""
        self._livekit_ctx = ctx
    
    def set_transcription_callback(self, callback) -> None:
        """Set callback for transcription forwarding to playground"""
        self._transcription_callback = callback
        logger.info("✅ Transcription callback set for playground forwarding")
    
    def _create_silence_frame(self, duration_ms: int = 100) -> rtc.AudioFrame:
        """Create a silence frame to interrupt current audio playback"""
        try:
            import numpy as np
            
            # Create silence for 100ms at 48kHz (LiveKit standard)
            sample_rate = 48000
            samples = int(sample_rate * duration_ms / 1000)  # 100ms of silence
            silence_data = np.zeros(samples, dtype=np.int16)
            
            return rtc.AudioFrame(
                data=silence_data.tobytes(),
                sample_rate=sample_rate,
                num_channels=1,
                samples_per_channel=samples
            )
        except Exception as e:
            logger.error(f"❌ Error creating silence frame: {e}")
            return None
    
    async def _ensure_connection(self) -> None:
        """Ensure connection to NextEVI (moved from agent code)"""
        if self._connected:
            return
            
        # Initialize HTTP session if needed
        if not self._http_session:
            self._http_session = aiohttp.ClientSession()
        
        # Create and connect websocket client
        self._websocket_client = NextEVIWebSocketClient(config=self._config)
        
        # PHASE 1 FIX: Set direct message handler for real-time processing
        self._websocket_client.set_message_handler(self._handle_nextevi_message)
        
        await self._websocket_client.connect()
        
        self._connected = True
        logger.info("NextEVI connection established with direct message processing")
    
    
    async def _handle_nextevi_message(self, message: dict[str, Any]) -> None:
        """Handle a message from NextEVI and emit appropriate events (moved from agent code)"""
        message_type = message.get("type")
        
        if message_type == "tts_chunk":
            await self._handle_tts_chunk(message)
        elif message_type == "transcription":
            await self._handle_transcription(message)
        elif message_type == "llm_response_chunk":
            await self._handle_llm_response_chunk(message)
        elif message_type == "emotion_update":
            await self._handle_emotion_update(message)
        elif message_type == "error":
            await self._handle_error(message)
        elif message_type == "tts_interruption":
            await self._handle_tts_interruption(message)
        elif message_type == "user_interruption":
            # Handle user interruption (same as tts_interruption)
            await self._handle_tts_interruption(message)
        elif message_type == "websocket.disconnect":
            await self._handle_websocket_disconnect(message)
        else:
            # Match React demo: log unknown messages but continue (don't treat as error)
            logger.info(f"Unknown message type: {message_type}, Message: {message}")
    
    async def _handle_tts_chunk(self, data: dict[str, Any]) -> None:
        """Handle TTS audio chunks from NextEVI with state tracking"""
        try:
            content = data.get("content", "")
            if content:
                # Track TTS playback state (like React demo)
                if not self._is_tts_playing:
                    self._is_tts_playing = True
                    logger.info("🔊 IMMEDIATE: TTS playback started")
                
                # Check if TTS was interrupted while processing this chunk
                if not self._is_tts_playing:
                    logger.info("🛑 IMMEDIATE: TTS chunk ignored due to interruption")
                    return
                
                # Convert NextEVI audio to LiveKit format
                audio_frame = self._decode_nextevi_audio(content)
                if audio_frame:
                    # Double-check if still playing before sending
                    if self._is_tts_playing:
                        # Send to audio output stream
                        self._audio_output_ch.send_nowait(audio_frame)
                    else:
                        logger.info("🛑 IMMEDIATE: Audio frame discarded due to interruption")
                    
        except Exception as e:
            logger.error(f"❌ TTS chunk handling error: {e}")
    
    def _decode_nextevi_audio(self, chunk_data: str) -> rtc.AudioFrame | None:
        """Decode NextEVI audio chunk to LiveKit AudioFrame (moved from agent code)"""
        try:
            import base64
            import numpy as np
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(chunk_data)
            
            # Convert to numpy array for processing
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # NextEVI is 24kHz, LiveKit expects 48kHz - upsample by factor of 2
            if len(audio_array) > 0:
                # Simple upsampling by repeating samples
                upsampled = np.repeat(audio_array, 2)
                
                # Create LiveKit AudioFrame
                return rtc.AudioFrame(
                    data=upsampled.tobytes(),
                    sample_rate=48000,
                    num_channels=1,
                    samples_per_channel=len(upsampled)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Audio decode error: {e}")
            return None
    
    async def _handle_transcription(self, message: dict[str, Any]) -> None:
        """Handle transcription message from NextEVI with playground callback support"""
        transcript = message.get("transcript", "")
        is_final = message.get("is_final", False)
        confidence = message.get("confidence", 1.0)
        
        if transcript:
            logger.info(f"🎙️ Transcription ({'final' if is_final else 'partial'}): {transcript}")
            
            # Try callback first (for playground text stream forwarding)
            if self._transcription_callback:
                try:
                    self._transcription_callback(transcript, is_final)
                    logger.info(f"✅ Transcription forwarded via callback: {transcript}")
                    return  # Skip direct room publishing if callback succeeds
                except Exception as e:
                    logger.error(f"❌ Transcription callback failed: {e}")
            
            # If no callback is set, log warning as transcription won't be forwarded
            logger.warning("⚠️ No transcription callback set - transcription will not be forwarded to playground")
    
    async def _handle_llm_response_chunk(self, message: dict[str, Any]) -> None:
        """Handle LLM response chunk from NextEVI - just log for debugging"""
        content = message.get("content", "")
        if content:
            logger.debug(f"💬 LLM response chunk: {content}")
    
    async def _handle_emotion_update(self, message: dict[str, Any]) -> None:
        """Handle emotion update from NextEVI (moved from agent code)"""
        emotions = message.get("emotions", [])
        if emotions:
            logger.debug(f"🎭 Emotion update: {emotions}")
    
    async def _handle_tts_interruption(self, message: dict[str, Any]) -> None:
        """Handle TTS interruption from NextEVI with immediate pipeline clearing (Phase 2 fix)"""
        logger.info("🚨 IMMEDIATE: TTS interruption received from server")
        
        # PHASE 2 FIX: Immediate interruption processing (bypass all queues)
        interruption_success = False
        
        # Stop TTS playback immediately
        if self._is_tts_playing:
            self._is_tts_playing = False
            logger.info("🔇 IMMEDIATE: TTS playback stopped due to interruption")
            
            # Clear audio output channel aggressively (React demo pattern)
            cleared_count = 0
            try:
                while True:
                    self._audio_output_ch.recv_nowait()  # Drain all pending frames
                    cleared_count += 1
                    if cleared_count > 1000:  # Safety limit
                        break
            except:
                pass  # Channel empty or closed
            
            logger.info(f"🗑️ IMMEDIATE: Cleared {cleared_count} pending TTS audio frames")
            
            # Send silence frames for immediate cutoff (if audio source available)
            if self._audio_source:
                try:
                    # Send multiple silence frames immediately
                    silence_tasks = []
                    for i in range(3):  # Reduced count for faster processing
                        silence_frame = self._create_silence_frame(duration_ms=20)  # Very short frames
                        if silence_frame:
                            task = asyncio.create_task(self._audio_source.capture_frame(silence_frame))
                            silence_tasks.append(task)
                    
                    # Wait for all silence frames to be sent (with timeout)
                    if silence_tasks:
                        await asyncio.wait_for(asyncio.gather(*silence_tasks), timeout=0.1)
                        interruption_success = True
                        logger.info("✅ IMMEDIATE: Silence frames sent successfully")
                except Exception as e:
                    logger.warning(f"⚠️ Silence frame sending failed: {e}")
            else:
                logger.warning("⚠️ No audio source available - interruption may be delayed")
        else:
            logger.info("🔇 IMMEDIATE: TTS was not playing, interruption ignored")
        
        # Log interruption content and success status
        content = message.get("content", "")
        if content:
            logger.info(f"🛑 Interruption content: {content}")
        
        logger.info(f"🎯 Interruption pipeline: {'✅ SUCCESS' if interruption_success else '⚠️ PARTIAL'}")
    
    async def _handle_error(self, message: dict[str, Any]) -> None:
        """Handle error message from NextEVI"""
        error_msg = message.get("error", "Unknown error")
        logger.error(f"NextEVI error: {error_msg}")
    
    async def _handle_websocket_disconnect(self, message: dict[str, Any]) -> None:
        """Handle websocket.disconnect messages from NextEVI backend and signal LiveKit"""
        code = message.get("code", "unknown")
        reason = message.get("reason", "")
        
        logger.info(f"🔌 NextEVI websocket.disconnect received: code={code}, reason='{reason}'")
        
        # Signal LiveKit to shutdown since NextEVI backend disconnected
        try:
            if self._livekit_ctx:
                logger.info("📡 Signaling LiveKit to shutdown due to NextEVI disconnect")
                self._livekit_ctx.shutdown(reason=f"NextEVI backend disconnected: {reason}")
            else:
                logger.warning("⚠️ Cannot signal LiveKit - no context reference")
        except Exception as e:
            logger.error(f"❌ Error signaling LiveKit shutdown: {e}")
        
        # Mark as disconnected to prevent further operations
        self._connected = False




