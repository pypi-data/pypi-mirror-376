#!/usr/bin/env python3
"""
NextEVI STT Bridge for LiveKit AgentSession Integration

This module creates a custom STT component that bridges NextEVI transcriptions
to LiveKit's AgentSession system, enabling proper transcription display in the playground.
"""

import asyncio
import logging
from typing import AsyncIterable, Union

from livekit import rtc
from livekit.agents import stt, utils

logger = logging.getLogger(__name__)


class NextEVISTT(stt.STT):
    """
    Custom STT component that bridges NextEVI transcriptions to AgentSession.
    
    This allows NextEVI transcriptions to be properly forwarded through LiveKit's
    built-in text stream system to the playground chat interface.
    """
    
    def __init__(self):
        super().__init__(
            capabilities=stt.STTCapabilities(
                streaming=True,
                interim_results=True
            )
        )
        self._transcription_queue: utils.aio.Chan[str] = utils.aio.Chan()
        self._is_final_queue: utils.aio.Chan[bool] = utils.aio.Chan()
        logger.info("✅ NextEVISTT component initialized for AgentSession integration")
    
    async def _recognize_impl(
        self, buffer: Union[rtc.AudioFrame, bytes], *, language: str | None = None
    ) -> stt.SpeechEvent:
        """
        Implementation of STT recognition - not used since we get transcriptions from NextEVI
        """
        # This method is required by the interface but won't be used in our case
        # since NextEVI handles the actual speech recognition
        pass
    
    def stream(self) -> "NextEVISTTStream":
        """Create a new STT stream for processing"""
        return NextEVISTTStream(self)
    
    def forward_transcription(self, transcript: str, is_final: bool):
        """
        Forward transcription from NextEVI to the STT stream
        
        Args:
            transcript: The transcribed text
            is_final: Whether this is a final transcription
        """
        try:
            # Send transcription to any active streams
            self._transcription_queue.send_nowait(transcript)
            self._is_final_queue.send_nowait(is_final)
            logger.debug(f"🎙️ NextEVISTT forwarded: {'final' if is_final else 'partial'} - {transcript}")
        except Exception as e:
            logger.error(f"❌ Failed to forward transcription: {e}")


class NextEVISTTStream(stt.SpeechStream):
    """STT stream that receives transcriptions from NextEVI"""
    
    def __init__(self, stt_instance: NextEVISTT):
        super().__init__(stt_instance._loop)
        self._stt = stt_instance
        self._event_queue: utils.aio.Chan[stt.SpeechEvent] = utils.aio.Chan()
        self._closed = False
        
        # Start the transcription forwarding task
        asyncio.create_task(self._forward_transcriptions())
        logger.debug("✅ NextEVISTTStream created and ready for transcriptions")
    
    async def _forward_transcriptions(self):
        """Forward transcriptions from NextEVI to speech events"""
        try:
            while not self._closed:
                # Wait for transcription from NextEVI
                transcript = await self._stt._transcription_queue.recv()
                is_final = await self._stt._is_final_queue.recv()
                
                # Create appropriate speech event
                if is_final:
                    event = stt.SpeechEvent(
                        type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                        alternatives=[
                            stt.SpeechData(
                                text=transcript,
                                confidence=1.0,
                                language="en"  # Default to English
                            )
                        ]
                    )
                else:
                    event = stt.SpeechEvent(
                        type=stt.SpeechEventType.INTERIM_TRANSCRIPT,
                        alternatives=[
                            stt.SpeechData(
                                text=transcript,
                                confidence=1.0,
                                language="en"
                            )
                        ]
                    )
                
                # Forward to AgentSession
                self._event_queue.send_nowait(event)
                logger.debug(f"📤 NextEVISTTStream sent {'final' if is_final else 'interim'} event: {transcript}")
                
        except Exception as e:
            logger.error(f"❌ Error in NextEVISTTStream transcription forwarding: {e}")
    
    async def aclose(self):
        """Close the STT stream"""
        self._closed = True
        await self._event_queue.aclose()
        logger.debug("🔒 NextEVISTTStream closed")
    
    def __aiter__(self) -> AsyncIterable[stt.SpeechEvent]:
        """Async iterator for speech events"""
        return self
    
    async def __anext__(self) -> stt.SpeechEvent:
        """Get next speech event"""
        if self._closed:
            raise StopAsyncIteration
        
        try:
            event = await self._event_queue.recv()
            return event
        except utils.aio.ChanClosed:
            raise StopAsyncIteration
    
    async def push_frame(self, frame: rtc.AudioFrame):
        """Push audio frame - not used since NextEVI handles audio processing"""
        pass