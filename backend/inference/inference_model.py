# inference_model.py -- Soham Deshpande, Intelligent Clinical Systems Inc.
# This file houses and runs the Edge Impulse Model
# Running this file will run a demo in the shell to text model viability


# Imports

import numpy as np
from edge_impulse_linux.audio import AudioImpulseRunner
from backend.core.config import CONFIDENCE_LEVEL, MODEL_PATH
from typing import Any


class Inference:

    def __init__(self, model_path: str = MODEL_PATH):
        """Initializes with model path and labels from item_map"""
        self._model_path = model_path
        self._runner = None
        self._labels = []
        self._frame_length = None


    def start(self) -> Any | None:
        """Loads the .eim model and starts the inference runner."""

        self._runner = AudioImpulseRunner(self._model_path)
        model_info = self._runner.init()

        self._labels = model_info['model_parameters']['labels']
        self._frame_length = model_info['model_parameters']['input_features_count']

        print(f'Inference : Model loaded')
        print(f'Inference : Labels: {self._labels}')

        return model_info


    def classify(self, audio_chunk: np.ndarray) -> tuple[str | None, float | None]:
        """
        Runs inference on a numpy float32 audio chunk.
        Returns (label, confidence) if confidence exceeds threshold,
        otherwise returns (None, None).
        """

        if self._runner is None:
            raise RuntimeError('Inference : Runner not started. Call start() first.')

        # Convert float32 [-1, 1] back to int16 for the runner
        audio_int16 = (audio_chunk * 32768).astype(np.int16)

        # Pad or trim to exact frame length the model expects
        if len(audio_int16) < self._frame_length:
            audio_int16 = np.pad(audio_int16, (0, self._frame_length - len(audio_int16)))
        elif len(audio_int16) > self._frame_length:
            audio_int16 = audio_int16[:self._frame_length]

        # Run classification
        result = self._runner.classify(audio_int16.tolist())

        if 'result' not in result or 'classification' not in result['result']:
            return None, None

        classification = result['result']['classification']

        # Find the label with the highest confidence
        best_label = max(classification, key=classification.get)
        best_confidence = classification[best_label]

        # Debugging to show live confidence values
        #print(f'Inference :  {classification}')

        # Filter out noise and low confidence results
        if best_label == 'Noise' or best_confidence < CONFIDENCE_LEVEL:
            return None, None

        return best_label, best_confidence


    def stop(self) -> None:
        """Stops the inference runner cleanly."""
        if self._runner:
            self._runner.stop()
            print('Inference : Runner stopped')


if __name__ == '__main__':

    from audio_capture import AudioCapture
    from audio_capture import SAMPLE_RATE, CHUNK_SIZE
    import time

    CHUNKS_PER_WINDOW = SAMPLE_RATE // CHUNK_SIZE
    COOLDOWN_SECONDS = 2.0

    last_detection_time = 0
    last_label = None

    print('Testing inference pipeline')
    print('Speak item names: ')

    inference = Inference()
    inference.start()

    capture = AudioCapture()
    capture.start()

    try:
        while True:
            chunks = [capture.read_chunk() for _ in range(CHUNKS_PER_WINDOW)]
            audio = np.concatenate(chunks)

            label, confidence = inference.classify(audio)

            now = time.time()
            if label and label != last_label or (now - last_detection_time) > COOLDOWN_SECONDS:
                if label and (now - last_detection_time) > COOLDOWN_SECONDS:
                    print(f'\nDetected: {label} (confidence: {confidence:.2%})\n')
                    last_label = label
                    last_detection_time = now

    except KeyboardInterrupt:
        capture.stop()
        inference.stop()