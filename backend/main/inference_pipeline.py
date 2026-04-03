# inference_pipeline.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Ties inference, LED control, and database together
# Checks rack lock status before running inference each cycle


# Imports

import asyncio
import numpy as np
from backend.core.config import COOLDOWN_TIME, SAMPLE_RATE, CHUNK_SIZE, MIC_INDEX
from backend.main.database import session
from backend.crud import get_item_by_label
from backend.crud import get_lock_status
from backend.main.events import pipeline_event
from backend.led.led_controller import LEDController
from backend.inference import AudioCapture
from backend.inference import Inference


# Constants

RACK_ID = 1
CHUNKS_PER_WINDOW = SAMPLE_RATE // CHUNK_SIZE


async def run_pipeline() -> None:
    """
    Main inference pipeline loop.
    Waits for pipeline_event before starting.
    Checks rack lock status each cycle — holds if locked.
    On label detection, looks up active items and triggers LED control.
    Cleans up audio and inference on exit or cancellation.
    """

    await pipeline_event.wait()
    print('Pipeline : Event received, starting pipeline')

    capture = AudioCapture(MIC_INDEX)
    inference = Inference()
    controller = LEDController()

    last_detection_time = 0.0
    last_label = None

    try:

        while True:
            async with session() as db:
                locked = await get_lock_status(db, RACK_ID)
                if locked is None or not locked:
                    break
                await asyncio.sleep(1.0)

                capture.start()
                inference.start()
                print('Pipeline : Started')

                while True:
                    locked = await get_lock_status(db, RACK_ID)
                    if locked:
                        capture.stop()
                        inference.stop()
                        controller.stop()
                        print('Pipeline : Shutdown, rack locked')
                        break

                    # Offload blocking audio read + inference to thread pool
                    loop = asyncio.get_event_loop()
                    chunks = await loop.run_in_executor(
                        None,
                        lambda: [capture.read_chunk() for _ in range(CHUNKS_PER_WINDOW)]
                    )
                    audio = np.concatenate(chunks)

                    label, confidence = await loop.run_in_executor(
                        None, inference.classify, audio
                    )

                    if label is None:
                        continue

                    now = loop.time()
                    if label == last_label and (now - last_detection_time) < COOLDOWN_TIME:
                        continue

                    last_label = label
                    last_detection_time = now

                    print(f'Pipeline : Detected {label} ({confidence:.2%})')

                    items = await get_item_by_label(db, label)
                    if items is None:
                        continue

                    active_items = [item for item in items if item.is_active]
                    if not active_items:
                        continue

                    for i, item in enumerate(active_items):

                        await controller.light_item(item.led_start,
                                                    item.led_end,
                                                    item.color_r,
                                                    item.color_g,
                                                    item.color_b,
                                                    clear_first=(i == 0))

                        print(f'Pipeline : LED trigger — item {item.name}, LEDs {item.led_start}–{item.led_end}')

    except asyncio.CancelledError:
        print('Pipeline : Cancelled, shutting down')

    finally:
        capture.stop()
        inference.stop()
        controller.stop()
        print('Pipeline : Shutdown complete')