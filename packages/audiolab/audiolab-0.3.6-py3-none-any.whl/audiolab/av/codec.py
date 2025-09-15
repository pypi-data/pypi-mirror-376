# Copyright (c) 2025 Zhendong Peng (pzd17@tsinghua.org.cn)
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

from collections import defaultdict
from typing import Dict, Set

import av
import numpy as np
from av import codecs_available
from av.codec.codec import UnknownCodecError

from audiolab.av.format import format_dtypes
from audiolab.av.typing import CodecEnum
from audiolab.av.utils import get_template


class CodecManager:
    """Manages audio codec enums with lazy initialization."""

    def __init__(self):
        self.canonical_names: Dict[str, Set[str]] = defaultdict(set)
        self.decodecs: Dict[str, av.Codec] = {}
        self.encodecs: Dict[str, av.Codec] = {}

        for codec in codecs_available:
            try:
                decoder_codec = av.Codec(codec)
                if decoder_codec.type != "audio":
                    continue
                if decoder_codec.audio_formats is not None:
                    canonical_name = decoder_codec.canonical_name
                    codec_name = decoder_codec.name
                    self.canonical_names[canonical_name].add(codec_name)
                    if codec_name not in self.decodecs:
                        self.decodecs[codec_name] = decoder_codec

                encoder_codec = av.Codec(codec, "w")
                if encoder_codec.audio_formats is not None:
                    canonical_name = encoder_codec.canonical_name
                    codec_name = encoder_codec.name
                    self.canonical_names[canonical_name].add(codec_name)
                    if codec_name not in self.encodecs:
                        self.encodecs[codec_name] = encoder_codec
            except UnknownCodecError:
                pass

        self.Decodec = CodecEnum("Decodec", self.decodecs)
        self.Encodec = CodecEnum("Encodec", self.encodecs)

        # Set docstrings
        template = get_template("codec")
        for name, codec in self.decodecs.items():
            getattr(self.Decodec, name).__doc__ = template.render(codec=codec, format_dtypes=format_dtypes, np=np)
        for name, codec in self.encodecs.items():
            getattr(self.Encodec, name).__doc__ = template.render(codec=codec, format_dtypes=format_dtypes, np=np)


# Create singleton instance
_codec_manager = CodecManager()

# Expose properties
canonical_names = _codec_manager.canonical_names
decodecs = _codec_manager.decodecs
encodecs = _codec_manager.encodecs
Decodec = _codec_manager.Decodec
Encodec = _codec_manager.Encodec
