# audio_capture.py -- Soham Deshpande, Intelligent Clinical Systems Inc.
# This file sets up an AudioCapture object to capture chunks of audio
# through auto-detected mic or indexed mic.
# Running this file directly will print all available mics
# and their respective indices so hard coding is allowed.


# Imports

import pyaudio
import numpy as np
from backend.core.config import SAMPLE_RATE, CHANNELS, CHUNK_SIZE


FORMAT = pyaudio.paInt16

# Auto Detecting will not display all mic options
# Run this file to display all options

def _find_usb_mic(audio_capture: pyaudio.PyAudio) -> int | None:
    """Auto-detects the first USB audio input device."""

    for j in range(audio_capture.get_device_count()):

        indices = audio_capture.get_device_info_by_index(j)
        name = indices.get('name', '').lower()

        if indices.get('maxInputChannels', 0) > 0:
            if 'usb' in name or 'external' in name or 'microphone' in name:
                print(f'AudioCapture : Auto-detected USB mic: {indices['name']} (index {j})')
                return j
    return None


class AudioCapture:

    def __init__(self, device_index: int = None):
        """Initializes AudioCapture with mic index that is auto-detected or preset"""

        self._pa = pyaudio.PyAudio()

        if device_index is None:
            self._device_index = _find_usb_mic(self._pa)
        else:
            self._device_index = device_index

        if self._device_index is None:
            raise RuntimeError(
                'Could not find a USB microphone. Run this file directly to \
                list available devices and set USB_MIC_DEVICE_INDEX manually.'
            )

        self._stream = None


    def start(self) -> None:
        """Opens the audio stream"""

        self._stream = self._pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=self._device_index,
            frames_per_buffer=CHUNK_SIZE,
        )

        print(f'AudioCapture : Stream started — {SAMPLE_RATE}Hz, mono, 16-bit')


    def read_chunk(self) -> np.ndarray:
        """
        Reads one chunk of audio from the mic.
        Returns a numpy array of float32 samples normalized to [-1.0, 1.0].
        """

        raw = self._stream.read(CHUNK_SIZE, exception_on_overflow=False)
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
        samples /= 32768.0
        return samples


    def stop(self) -> None:
        """Closes the audio stream cleanly."""

        if self._stream:
            self._stream.stop_stream()
            self._stream.close()

        self._pa.terminate()
        print('AudioCapture : Stream stopped')


if __name__ == '__main__':

    pa = pyaudio.PyAudio()
    print('Available audio input devices:\n')

    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)

        if info.get("maxInputChannels", 0) > 0:
            print(f"  [{i}] {info['name']}")

    pa.terminate()
    print('\nSet USB_MIC_DEVICE_INDEX to the index of your USB mic')