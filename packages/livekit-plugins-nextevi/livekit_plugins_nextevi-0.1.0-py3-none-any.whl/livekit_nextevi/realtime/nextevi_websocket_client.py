from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK
import websockets.protocol

from livekit import rtc
from livekit.agents import APIConnectionError, utils

logger = logging.getLogger(__name__)



class NextEVIWebSocketClient:
    """
    WebSocket client for NextEVI platform communication
    
    Handles real-time communication with NextEVI's voice AI platform,
    including audio streaming, message handling, and session management.
    """
    
    def __init__(
        self,
        config,  # NextEVIConfig
    ) -> None:
        """
        Initialize NextEVI WebSocket client with all complexity moved from agent code
        
        Args:
            config: NextEVI configuration object
        """
        self._config = config
        
        # WebSocket connection
        self._websocket: Optional[websockets.WebSocketServerProtocol] = None
        self._connection_id = None  # Will be generated in _build_websocket_url()
        self._is_connected = False
        
        
        
        # Direct message processing callback (Phase 1 fix)
        self._message_handler_callback = None
        
        # Connection tasks
        self._receive_task: Optional[asyncio.Task] = None
        
        # Audio streaming counters (moved from agent code)
        self._audio_chunk_counter = 0
        self._tts_chunk_count = 0
        
        logger.info("NextEVI WebSocket client initialized")
    
    def set_message_handler(self, callback):
        """Set direct message processing callback for real-time handling (Phase 1 fix)"""
        self._message_handler_callback = callback
    
    @property
    def is_connected(self) -> bool:
        """Check if websocket is connected (React demo style)"""
        # Simple check like React demo: this.isConnected && this.websocket?.readyState === WebSocket.OPEN
        return (self._is_connected and 
                self._websocket is not None and 
                self._websocket.state == websockets.protocol.State.OPEN)
    
    @property
    def connection_id(self) -> Optional[str]:
        """Get the connection ID"""
        return self._connection_id
    
    async def connect(self) -> None:
        """Connect to NextEVI websocket with automatic retry (moved from agent code)"""
        await self._ensure_connection()
        
        # Start message processing task (like React demo - simple approach)
        self._receive_task = asyncio.create_task(self._message_processing_loop())
        
        logger.info(f"NextEVI WebSocket client connected: {self._connection_id}")
    
    async def _ensure_connection(self) -> None:
        """Ensure WebSocket connection is established (moved from agent code)"""
        if self.is_connected:
            return
        
        try:
            # Build websocket URL with authentication
            ws_url = self._build_websocket_url()
            headers = self._build_headers()
            
            logger.info(f"🔗 Connecting to NextEVI: {ws_url[:50]}...")
            
            # Connect to websocket
            self._websocket = await websockets.connect(
                ws_url,
                additional_headers=headers,
                ping_interval=30,  # Send ping every 30 seconds
                ping_timeout=10,   # Wait 10 seconds for pong
                close_timeout=10,  # Wait 10 seconds for close
            )
            
            # Configure session for voice interaction using NextEVI format
            session_config = {
                "type": "session_settings",
                "sample_rate": 24000,
                "channels": 1,
                "encoding": "linear16"
            }
            
            await self._websocket.send(json.dumps(session_config))
            
            self._is_connected = True
            
            logger.info("✅ NextEVI WebSocket connected and configured")
            
        except Exception as e:
            self._is_connected = False
            self._websocket = None
            raise APIConnectionError(f"Failed to connect to NextEVI: {e}") from e
    
    async def disconnect(self) -> None:
        """Disconnect from NextEVI websocket"""
        if not self._is_connected:
            return
        
        logger.info("Disconnecting from NextEVI")
        
        self._is_connected = False
        
        # Cancel background tasks
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        
        # Close websocket
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
        
        # Clear state
        self._connection_id = None
        
        logger.info("Disconnected from NextEVI")
    
    def _build_websocket_url(self) -> str:
        """Build the websocket URL using proper config authentication (matching React demo format)"""
        import random
        import string
        # Generate new session ID in React demo format exactly: voice_{timestamp}_{random9chars}
        # React demo: `voice_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        timestamp = int(time.time() * 1000)
        # Generate 9-character random string like JavaScript Math.random().toString(36).substr(2, 9)
        random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
        self._connection_id = f"voice_{timestamp}_{random_chars}"
        # Use the config's proper authentication method that handles JWT
        return self._config.get_websocket_url(self._connection_id)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers using proper config authentication (like working agent)"""
        # Use the config's proper authentication method
        return self._config.get_connection_headers()
    
    async def _send_session_settings(self) -> None:
        """Send initial session settings to NextEVI"""
        settings_message = {
            'type': 'session_settings',
            'message_id': str(uuid.uuid4()),
            'timestamp': time.time(),
            'sample_rate': 24000,
            'channels': 1,
            'encoding': 'linear16',
        }
        
        await self._send_message(settings_message)
        logger.debug("Sent session settings to NextEVI")
    
    async def _send_message(self, message: Dict[str, Any]) -> None:
        """Send a message to NextEVI"""
        if not self._is_connected or not self._websocket:
            raise RuntimeError("Not connected to NextEVI")
        
        try:
            message_json = json.dumps(message)
            await self._websocket.send(message_json)
            logger.debug(f"Sent message to NextEVI: {message.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to send message to NextEVI: {e}")
            raise
    
    
    
    async def send_audio(self, audio_frame: rtc.AudioFrame) -> None:
        """Send audio with format conversion to NextEVI format (24kHz mono 16-bit)"""
        if not self.is_connected:
            logger.warning("Cannot send audio: not connected to NextEVI")
            return
        
        try:
            self._audio_chunk_counter += 1
            
            # DEBUG: Log LiveKit AudioFrame properties (first 5 frames only)
            if self._audio_chunk_counter <= 5:
                logger.info(f"🔍 LiveKit AudioFrame DEBUG #{self._audio_chunk_counter}:")
                logger.info(f"  - Sample Rate: {audio_frame.sample_rate}")
                logger.info(f"  - Channels: {audio_frame.num_channels}")
                logger.info(f"  - Samples per Channel: {audio_frame.samples_per_channel}")
                logger.info(f"  - Data Size: {len(audio_frame.data)} bytes")
            
            # Convert LiveKit audio to NextEVI format (24kHz mono 16-bit)
            converted_audio = self._convert_to_nextevi_format(audio_frame)
            
            if converted_audio and len(converted_audio) > 0:
                # Send converted audio data to WebSocket (matching React demo exactly)
                await self._websocket.send(converted_audio)
                
                # Enhanced conversion logging (first 5 frames only)
                if self._audio_chunk_counter <= 5:
                    input_bytes = len(audio_frame.data)
                    output_bytes = len(converted_audio)
                    ratio = output_bytes / input_bytes if input_bytes > 0 else 0
                    logger.info(f"🔄 CONVERSION #{self._audio_chunk_counter}: {input_bytes} -> {output_bytes} bytes (ratio: {ratio:.3f})")
                    # Check if ratio makes sense based on format conversion
                    if abs(ratio - 0.5) < 0.1:  # 48kHz->24kHz with same bit depth
                        logger.info(f"✅ Sample rate conversion: 48kHz->24kHz (ratio: {ratio:.3f})")
                    elif abs(ratio - 2.0) < 0.1:  # 8-bit->16-bit + 48kHz->24kHz
                        logger.info(f"✅ Format + sample rate conversion: 8-bit->16-bit + 48kHz->24kHz (ratio: {ratio:.3f})")
                    elif abs(ratio - 1.0) < 0.1:  # No significant conversion
                        logger.info(f"✅ Minimal conversion needed (ratio: {ratio:.3f})")
                    else:
                        logger.warning(f"⚠️ Unexpected conversion ratio: {ratio:.3f}")
            
            # Minimal logging for debugging (every 100th chunk)
            if self._audio_chunk_counter % 100 == 0:
                logger.debug(f"📤 [SEND] Audio streaming active (sent #{self._audio_chunk_counter} chunks)")
                
        except Exception as e:
            logger.error(f"❌ Error sending converted audio: {e}")
    
    def _convert_to_nextevi_format(self, audio_frame: rtc.AudioFrame) -> bytes:
        """Convert LiveKit AudioFrame to NextEVI format using LiveKit's AudioResampler"""
        try:
            import numpy as np
            
            # Audio validation - check for non-zero samples
            audio_samples = np.frombuffer(audio_frame.data, dtype=np.int16)
            non_zero_count = np.count_nonzero(audio_samples)
            
            # Debug logging for first few frames
            if self._audio_chunk_counter <= 3:
                logger.info(f"🔍 INPUT: {audio_frame.sample_rate}Hz, {audio_frame.num_channels}ch, {len(audio_samples)} samples")
                logger.info(f"🎵 Audio data: {non_zero_count}/{len(audio_samples)} non-zero samples")
            
            # Skip processing if audio is complete silence (optimization)
            if non_zero_count == 0:
                if self._audio_chunk_counter <= 10:  # Only log first 10 silence frames
                    logger.debug(f"🔇 Skipping silence frame #{self._audio_chunk_counter}")
                return b''  # Return empty bytes for silence
            
            # Convert multi-channel to mono if needed
            if audio_frame.num_channels > 1:
                audio_samples = audio_samples.reshape(-1, audio_frame.num_channels).mean(axis=1).astype(np.int16)
                if self._audio_chunk_counter <= 3:
                    logger.info(f"🔄 Converted {audio_frame.num_channels}ch → 1ch mono")
            
            # Use LiveKit AudioResampler for high-quality conversion
            if audio_frame.sample_rate != 24000:
                # Initialize resampler if not already done
                if not hasattr(self, '_audio_resampler'):
                    self._audio_resampler = rtc.AudioResampler(
                        input_rate=audio_frame.sample_rate,
                        output_rate=24000, 
                        num_channels=1,
                        quality=rtc.AudioResamplerQuality.MEDIUM
                    )
                    logger.info(f"🎛️ AudioResampler initialized: {audio_frame.sample_rate}Hz → 24kHz")
                
                # Create new AudioFrame for resampling
                mono_frame = rtc.AudioFrame(
                    data=audio_samples.tobytes(),
                    sample_rate=audio_frame.sample_rate,
                    num_channels=1,
                    samples_per_channel=len(audio_samples)
                )
                
                # Resample using LiveKit's high-quality resampler
                resampled_frames = self._audio_resampler.push(mono_frame)
                
                if resampled_frames:
                    # Combine all resampled frames
                    resampled_data = b''
                    total_samples = 0
                    for frame in resampled_frames:
                        resampled_data += frame.data
                        total_samples += frame.samples_per_channel
                    
                    if self._audio_chunk_counter <= 3:
                        original_samples = len(audio_samples) 
                        ratio = audio_frame.sample_rate / 24000
                        logger.info(f"🔄 Resampled: {audio_frame.sample_rate}Hz→24kHz, {original_samples}→{total_samples} samples (ratio: {ratio:.2f})")
                    
                    return resampled_data
                else:
                    # No resampled data available yet (buffering)
                    if self._audio_chunk_counter <= 5:
                        logger.debug(f"📦 Resampler buffering frame #{self._audio_chunk_counter}")
                    return b''
            else:
                # Already 24kHz, just convert mono samples to bytes
                converted_bytes = audio_samples.tobytes()
                if self._audio_chunk_counter <= 3:
                    logger.info(f"✅ No resampling needed: already 24kHz")
                return converted_bytes
            
        except Exception as e:
            logger.error(f"❌ Audio conversion error: {e}")
            # Fallback: return empty bytes instead of potentially corrupted data
            return b''
    
    
    async def _send_message_with_error_handling(self, message: Dict[str, Any]) -> None:
        """Send message with connection error handling (moved from agent code)"""
        try:
            message_json = json.dumps(message)
            await self._websocket.send(message_json)
            
        except ConnectionClosedError as e:
            logger.warning(f"🔌 WebSocket closed during send: {e.code} - {e.reason}")
            self._is_connected = False
                
        except Exception as e:
            logger.error(f"❌ Error sending message to NextEVI: {e}")
            # Check if this is a connection-related error
            if "websocket" in str(e).lower() or "connection" in str(e).lower():
                self._is_connected = False
    
    
    
    
    async def _message_processing_loop(self) -> None:
        """Process incoming messages from NextEVI with real-time direct processing"""
        try:
            while self._is_connected:
                if not self._websocket:
                    await asyncio.sleep(0.1)
                    continue
                
                try:
                    # Check connection state immediately (like React demo)
                    if (self._websocket.state != websockets.protocol.State.OPEN):
                        logger.error(f"⚡ IMMEDIATE: WebSocket state changed to {self._websocket.state}")
                        self._is_connected = False
                        break
                    
                    # Receive message with much shorter timeout for real-time processing
                    message_raw = await asyncio.wait_for(
                        self._websocket.recv(), timeout=0.1
                    )
                    
                    # Parse JSON message
                    message = json.loads(message_raw)
                    
                    # PHASE 1 FIX: Direct message processing (eliminate dual loop)
                    await self._process_message_immediately(message)
                    
                    # Yield control to event loop for responsiveness
                    await asyncio.sleep(0)
                    
                except asyncio.TimeoutError:
                    # Yield control on timeout to prevent blocking
                    await asyncio.sleep(0)
                    continue
                except ConnectionClosedError as e:
                    logger.error(f"⚡ IMMEDIATE: NextEVI WebSocket closed: {e.code} - {e.reason}")
                    self._is_connected = False
                    break
                except ConnectionClosedOK:
                    logger.info("⚡ IMMEDIATE: NextEVI WebSocket closed normally - updating status")
                    self._is_connected = False
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON from NextEVI: {e}")
                except Exception as e:
                    logger.error(f"❌ NextEVI message processing error: {e}")
                    break
                    
        except asyncio.CancelledError:
            logger.debug("Message processing loop cancelled")
        except Exception as e:
            logger.error(f"❌ Fatal error in message processing loop: {e}")
    
    async def _process_message_immediately(self, message: Dict[str, Any]) -> None:
        """Process message immediately for real-time responsiveness (Phase 1 fix)"""
        msg_type = message.get("type", "unknown")
        
        # Log non-TTS messages for debugging
        if msg_type not in ["tts_chunk"]:
            logger.debug(f"📨 [RECV] {msg_type}")
        
        # Priority handling for interruptions (immediate processing)
        if msg_type in ["tts_interruption", "user_interruption"]:
            logger.info(f"🚨 IMMEDIATE INTERRUPTION: {msg_type}")
            if self._message_handler_callback:
                await self._message_handler_callback(message)
            return
        
        # Direct callback for real-time processing
        if self._message_handler_callback:
            await self._message_handler_callback(message)
        else:
            logger.warning("⚠️ No message handler callback set, dropping message")

    async def send_text_message(self, text: str) -> None:
        """Send a text message to NextEVI (for testing/debugging)"""
        if not self._is_connected:
            raise RuntimeError("Not connected to NextEVI")
        
        message = {
            'type': 'text_input',
            'message_id': str(uuid.uuid4()),
            'timestamp': time.time(),
            'text': text,
        }
        
        await self._send_message(message)
    
    async def interrupt_generation(self) -> None:
        """Interrupt current generation"""
        if not self._is_connected:
            raise RuntimeError("Not connected to NextEVI")
        
        interrupt_message = {
            'type': 'interrupt',
            'message_id': str(uuid.uuid4()),
            'timestamp': time.time(),
        }
        
        await self._send_message(interrupt_message)
        logger.debug("Sent interrupt to NextEVI")