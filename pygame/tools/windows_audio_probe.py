# SPDX-License-Identifier: GPL-3.0-or-later
"""Preflight the actual native audio interfaces before a Windows game launch.

A failed check only makes the BAT launcher use the game's existing --silent mode.
It must not alter game engine behavior, configure audio devices, or copy DLLs.
"""

import ctypes

from pygame._sdl2 import audio

from rich4.runtime_library import 本地运行库_类
from rich4.wave_decoder import 原波形_类


def main() -> int:
    try:
        # Missing FluidSynth raises at game startup, even when PCM SDL3 is present.
        fluid = 本地运行库_类.api_选择("fluidsynth", "RICH4_FLUIDSYNTH_LIBRARY")
        if fluid is None:
            return 1
        ctypes.CDLL(fluid)
        # Verify the same Pygame SDL2 symbol lookup that the live device uses.
        getattr(ctypes.CDLL(audio.__file__), "SDL_OpenAudioDevice")
        # The actual WAV backend also checks SDL3 availability and version.
        原波形_类()
        return 0
    except (OSError, AttributeError, RuntimeError, ValueError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
