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
from backend.main.events import pipeline_event, last_detected
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
    Fresh AudioCapture/Inference/LEDController instances are created each
    lock→unlock cycle because most audio/ML backends do not support
    stop() followed by start() on the same object.
    On label detection, looks up active items and triggers LED control.
    """

    await pipeline_event.wait()
    print('Pipeline : Event received, starting pipeline')

    loop = asyncio.get_event_loop()

    last_detection_time = 0.0
    last_label = None

    # Kept as None until instantiated inside the loop; used by finally for cleanup
    capture = None
    inference = None
    controller = None

    try:

        while True:

            # Wait until the rack is unlocked
            async with session() as db:
                while True:
                    locked = await get_lock_status(db, RACK_ID)
                    if locked is None or not locked:
                        break
                    await asyncio.sleep(1.0)

            # Fresh instances every cycle — avoids stop()/start() re-use crashes
            capture = AudioCapture(MIC_INDEX)
            inference = Inference()
            controller = LEDController()

            # Run start() in executor so the event loop stays responsive to cancellation
            try:
                await loop.run_in_executor(None, capture.start)
                await loop.run_in_executor(None, inference.start)
                print('Pipeline : Started')

            except Exception as start_err:
                print(f'Pipeline : Failed to start capture/inference — {start_err}')
                capture = inference = controller = None
                await asyncio.sleep(3.0)
                continue

            # Inference loop — runs until the rack is locked again
            async with session() as db:

                while True:
                    locked = await get_lock_status(db, RACK_ID)
                    if locked:
                        for fn, name in [(capture.stop, 'capture'),
                                         (inference.stop, 'inference'),
                                         (controller.stop, 'controller')]:
                            try:
                                await loop.run_in_executor(None, fn)

                            except Exception as e:
                                print(f'Pipeline : Error stopping {name} on lock — {e}')

                        capture = inference = controller = None
                        print('Pipeline : Paused, rack locked')
                        break

                    # Offload blocking audio read + inference to thread pool
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

                    clear = False
                    for item in active_items:
                        while not clear:
                            controller.clear() # Clear last lit item
                            clear = True

                        # Light top divider strip
                        await controller.light_item(
                            item.led_start, item.led_end,
                            item.color_r, item.color_g, item.color_b
                        )
                        # Light bottom divider strip (if assigned)
                        if item.led_start_b or item.led_end_b:
                            await controller.light_item(
                                item.led_start_b, item.led_end_b,
                                item.color_r, item.color_g, item.color_b
                            )

                        # Update in-memory last-detected state for the display screen
                        last_detected['item_id'] = item.item_id
                        last_detected['item_name'] = item.name
                        last_detected['item_label'] = item.label

                        print(f'Pipeline : LED trigger — item {item.name}, LEDs {item.led_start}–{item.led_end}')

    except asyncio.CancelledError:
        print('Pipeline : Cancelled, shutting down')

    except Exception as e:
        print(f'Pipeline : Unhandled error — {e}')

    finally:
        # Clean up whatever instances exist at shutdown time
        for obj, name in [(capture, 'capture'),
                          (inference, 'inference'),
                          (controller, 'controller')]:
            if obj is None:
                continue
            try:
                await loop.run_in_executor(None, obj.stop)
            except Exception as e:
                print(f'Pipeline : Error stopping {name} — {e}')
        print('Pipeline : Shutdown complete')