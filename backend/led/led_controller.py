# led_controller.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# Controls WS2812B LED strip via rpi_ws281x
# Handles item lighting, timeout, and full strip clear


# Imports

import asyncio
from backend.core.config import LED_PIN, LED_TOTAL

try:
    from rpi_ws281x import PixelStrip, Color
    _RPI_AVAILABLE = True
except ImportError:
    _RPI_AVAILABLE = False
    print('LEDController : rpi_ws281x not available — running in stub mode (Mac/dev)')


# Constants

LED_FREQ_HZ = 800000    # Signal frequency (WS2812B standard)
LED_DMA = 10            # DMA channel
LED_BRIGHTNESS = 255    # Full brightness
LED_INVERT = False      # No signal inversion needed (direct data line)
LED_CHANNEL = 0         # PWM channel 0
LED_TIMEOUT = 10.0      # Seconds before LEDs auto-clear


class LEDController:

    def __init__(self):
        """Initializes the WS2812B LED strip"""

        self._timeout_task: asyncio.Task | None = None
        if _RPI_AVAILABLE:
            try:
                self._strip = PixelStrip(
                    LED_TOTAL,
                    LED_PIN,
                    LED_FREQ_HZ,
                    LED_DMA,
                    LED_INVERT,
                    LED_BRIGHTNESS,
                    LED_CHANNEL
                )
                self._strip.begin()
                print(f'LEDController : Strip initialized — {LED_TOTAL} LEDs on GPIO {LED_PIN}')
            except Exception as e:
                self._strip = None
                print(f'LEDController : Hardware init failed ({e}) — running in stub mode')
        else:
            self._strip = None
            print('LEDController : Stub initialized')


    def _set_range(self, led_start: int, led_end: int, r: int, g: int, b: int) -> None:
        """Sets a range of LEDs to a color and shows immediately."""

        if not _RPI_AVAILABLE:
            return
        for i in range(led_start, led_end + 1):
            self._strip.setPixelColor(i, Color(r, g, b))
        self._strip.show()


    def clear(self) -> None:
        """Turns off all LEDs on the strip."""

        if not _RPI_AVAILABLE:
            print('LEDController : Strip cleared (stub)')
            return
        for i in range(LED_TOTAL):
            self._strip.setPixelColor(i, Color(0, 0, 0))
        self._strip.show()
        print('LEDController : Strip cleared')


    async def _timeout_clear(self) -> None:
        """Waits for LED_TIMEOUT seconds then clears the strip."""

        try:
            await asyncio.sleep(LED_TIMEOUT)
            self.clear()
        except asyncio.CancelledError:
            pass


    async def light_item(self, led_start: int, led_end: int, r: int, g: int, b: int) -> None:
        """
        Lights a range of LEDs with the given color.
        Cancels any existing timeout and starts a fresh one.
        Returns immediately — timeout runs as background task.

        Args:
            led_start: First LED index
            led_end: Last LED index
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """

        # Cancel previous timeout if still running
        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()
            await asyncio.gather(self._timeout_task, return_exceptions=True)

        self._set_range(led_start, led_end, r, g, b)
        print(f'LEDController : Lit LEDs {led_start}–{led_end} RGB({r},{g},{b})')

        self._timeout_task = asyncio.create_task(self._timeout_clear())


    def stop(self) -> None:
        """Cancels timeout task and clears strip on shutdown."""

        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()

        self.clear()
        print('LEDController : Stopped')