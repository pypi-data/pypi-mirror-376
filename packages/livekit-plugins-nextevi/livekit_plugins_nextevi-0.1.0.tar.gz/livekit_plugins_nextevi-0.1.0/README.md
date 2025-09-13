# LiveKit NextEVI Plugin

A LiveKit Agents plugin for NextEVI's voice AI platform, providing real-time speech-to-speech capabilities with advanced voice AI features.

## Features

- **Real-time speech-to-speech** - Direct audio input to voice response
- **Voice interruption support** - Natural conversation with interruption handling  
- **Multiple TTS engines** - Orpheus, Ethos, Kokoro, and more
- **Emotion analysis** - Real-time emotion detection and adaptation
- **Voice cloning** - Custom voice synthesis capabilities
- **Knowledge base integration** - Contextual AI responses
- **LiveKit Agents integration** - Seamless integration with LiveKit's AgentSession

## Installation

```bash
pip install livekit-plugins-nextevi
```

## Quick Start

### Basic Usage

```python
import asyncio
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit_nextevi import NextEVIRealtimeModel

async def agent_entrypoint(ctx: JobContext):
    # Connect to room
    await ctx.connect()
    
    # Create NextEVI model
    model = NextEVIRealtimeModel(
        api_key="your_nextevi_api_key",  # Set via environment: NEXTEVI_API_KEY
        config_id="your_config_id",     # Set via environment: NEXTEVI_CONFIG_ID
        project_id="your_project_id"    # Set via environment: NEXTEVI_PROJECT_ID (optional)
    )
    
    # Set up audio output
    audio_source = rtc.AudioSource(sample_rate=48000, num_channels=1)
    track = rtc.LocalAudioTrack.create_audio_track("nextevi-voice", audio_source)
    await ctx.room.local_participant.publish_track(track)
    
    # Configure model with audio source
    model.set_audio_source(audio_source)
    model.set_livekit_context(ctx)
    
    # Handle incoming audio
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            async def process_audio():
                audio_stream = rtc.AudioStream(track)
                async for event in audio_stream:
                    if isinstance(event, rtc.AudioFrameEvent):
                        # Send audio to NextEVI for processing
                        await model.push_audio(event.frame)
            
            asyncio.create_task(process_audio())
    
    # Stream NextEVI audio output to LiveKit
    async def stream_audio_output():
        audio_stream = model.audio_output_stream()
        async for audio_frame in audio_stream:
            await audio_source.capture_frame(audio_frame)
    
    asyncio.create_task(stream_audio_output())
    
    # Keep running
    await asyncio.Future()

# Run the agent
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=agent_entrypoint))
```

### With AgentSession (Recommended)

For better integration with LiveKit's playground and transcription display:

```python
import asyncio
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, AgentSession
from livekit_nextevi import NextEVIRealtimeModel, NextEVISTT

async def agent_entrypoint(ctx: JobContext):
    await ctx.connect()
    
    # Create custom STT for transcription forwarding
    nextevi_stt = NextEVISTT()
    
    # Create NextEVI model
    model = NextEVIRealtimeModel(
        api_key="your_nextevi_api_key",
        config_id="your_config_id",
        project_id="your_project_id"
    )
    
    # Bridge NextEVI transcriptions to STT
    def on_transcription(transcript: str, is_final: bool):
        nextevi_stt.forward_transcription(transcript, is_final)
    
    model.set_transcription_callback(on_transcription)
    
    # Create AgentSession
    session = AgentSession(
        stt=nextevi_stt,  # Custom STT for transcription forwarding
        llm=model,        # NextEVI handles LLM + TTS
    )
    
    # Set up audio output (same as basic usage)
    audio_source = rtc.AudioSource(sample_rate=48000, num_channels=1)
    track = rtc.LocalAudioTrack.create_audio_track("nextevi-voice", audio_source)
    await ctx.room.local_participant.publish_track(track)
    
    model.set_audio_source(audio_source)
    model.set_livekit_context(ctx)
    
    # Handle audio input (same as basic usage)
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            async def process_audio():
                audio_stream = rtc.AudioStream(track)
                async for event in audio_stream:
                    if isinstance(event, rtc.AudioFrameEvent):
                        await model.push_audio(event.frame)
            asyncio.create_task(process_audio())
    
    # Stream audio output (same as basic usage)
    async def stream_audio_output():
        audio_stream = model.audio_output_stream()
        async for audio_frame in audio_stream:
            await audio_source.capture_frame(audio_frame)
    
    asyncio.create_task(stream_audio_output())
    await asyncio.Future()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=agent_entrypoint))
```

## Configuration

### Environment Variables

Set these environment variables to configure the plugin:

```bash
export NEXTEVI_API_KEY="your_api_key_here"
export NEXTEVI_CONFIG_ID="your_config_id_here" 
export NEXTEVI_PROJECT_ID="your_project_id_here"  # Optional
```

### NextEVIRealtimeModel Options

```python
model = NextEVIRealtimeModel(
    api_key="your_api_key",           # Required: NextEVI API key
    config_id="your_config_id",       # Required: NextEVI configuration ID
    project_id="your_project_id",     # Optional: NextEVI project ID
    tts_engine="orpheus",             # TTS engine: orpheus, ethos, kokoro
    voice_id="leo",                   # Voice ID for TTS
    llm_provider="anthropic",         # LLM provider: anthropic, openai
    temperature=0.8,                  # LLM temperature
    speech_speed=1.0,                 # TTS speed multiplier
    enable_emotion_analysis=True,     # Enable emotion analysis
    enable_knowledge_base=True,       # Enable knowledge base integration
    enable_interruption=True,         # Enable voice interruption
    recording_enabled=False,          # Enable session recording
)
```

## Key Methods

### NextEVIRealtimeModel

- `push_audio(audio_frame)` - Send audio frame for processing
- `audio_output_stream()` - Get stream of TTS audio output
- `set_audio_source(audio_source)` - Configure LiveKit audio source
- `set_transcription_callback(callback)` - Set transcription forwarding callback
- `commit_audio()` - Commit audio input (no-op for NextEVI)

### NextEVISTT (Internal)

- `forward_transcription(transcript, is_final)` - Forward transcription to AgentSession

## Requirements

- Python 3.9+
- LiveKit Agents 1.2.8+
- NextEVI API account and credentials

## License

Apache 2.0

## Support

- [NextEVI Documentation](https://docs.nextevi.com)
- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [GitHub Issues](https://github.com/nextevi/livekit-nextevi/issues)