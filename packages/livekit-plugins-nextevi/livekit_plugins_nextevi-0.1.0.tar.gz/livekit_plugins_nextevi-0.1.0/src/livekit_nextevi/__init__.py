# Copyright 2023 LiveKit, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""NextEVI plugin for LiveKit Agents

Support for NextEVI's voice AI platform with real-time speech-to-speech capabilities.

Provides integration with NextEVI's websocket API, supporting advanced features like
emotion analysis, voice cloning, knowledge base integration, and multiple TTS engines.

See https://nextevi.com/ for more information about the NextEVI platform.
"""

from . import realtime
from .version import __version__
from .realtime.nextevi_realtime_model import NextEVIRealtimeModel
from .nextevi_stt import NextEVISTT

__all__ = [
    "realtime",
    "NextEVIRealtimeModel",
    "NextEVISTT",
    "__version__",
]

from livekit.agents import Plugin

import logging

logger = logging.getLogger(__name__)


class NextEVIPlugin(Plugin):
    def __init__(self) -> None:
        super().__init__(__name__, __version__, __package__, logger)


Plugin.register_plugin(NextEVIPlugin())

# Cleanup docs of unexported modules
_module = dir()
NOT_IN_ALL = [m for m in _module if m not in __all__]

__pdoc__ = {}

for n in NOT_IN_ALL:
    __pdoc__[n] = False
