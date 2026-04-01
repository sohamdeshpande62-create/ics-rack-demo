# rpi_ws281x_compat.py
# ctypes wrapper around libws2811.so (pi5 branch of rpi_ws281x)
# Provides PixelStrip and Color API compatible with the standard rpi_ws281x package.
#
# Install as rpi_ws281x on the Pi:
#   sudo cp backend/led/rpi_ws281x_compat.py /usr/lib/python3/dist-packages/rpi_ws281x.py

import ctypes
import ctypes.util

# Load the shared library built from the pi5 rpi_ws281x branch
_lib = ctypes.CDLL('/usr/local/lib/libws2811.so')

# Strip type constants (color byte order)
WS2812_STRIP       = 0x00081000  # GRB — WS2812B default
SK6812_STRIP_RGBW  = 0x18081000

WS2811_SUCCESS     = 0


class _ws2811_channel_t(ctypes.Structure):
    _fields_ = [
        ('gpionum',    ctypes.c_int),
        ('invert',     ctypes.c_int),
        ('count',      ctypes.c_int),
        ('strip_type', ctypes.c_int),
        ('leds',       ctypes.POINTER(ctypes.c_uint32)),
        ('brightness', ctypes.c_uint8),
        ('wshift',     ctypes.c_uint8),
        ('rshift',     ctypes.c_uint8),
        ('gshift',     ctypes.c_uint8),
        ('bshift',     ctypes.c_uint8),
        ('gamma',      ctypes.c_void_p),
    ]


class _ws2811_t(ctypes.Structure):
    _fields_ = [
        ('freq',    ctypes.c_uint64),
        ('dmanum',  ctypes.c_int),
        ('channel', _ws2811_channel_t * 2),
    ]


# Set return types
_lib.ws2811_init.restype   = ctypes.c_int
_lib.ws2811_render.restype = ctypes.c_int
_lib.ws2811_wait.restype   = ctypes.c_int
_lib.ws2811_fini.restype   = None


def Color(red, green, blue, white=0):
    """Pack r, g, b (and optional w) into a 32-bit LED color value."""
    return (white << 24) | (red << 16) | (green << 8) | blue


class PixelStrip:
    """
    Wraps the ws2811 C library to drive a WS2812B strip.
    Constructor signature matches the standard rpi_ws281x package.
    """

    def __init__(self, num, pin, freq_hz=800000, dma=5, invert=False,
                 brightness=255, channel=0, strip_type=None, gamma=None):
        self._num     = num
        self._channel = channel

        self._ws              = _ws2811_t()
        self._ws.freq         = freq_hz
        self._ws.dmanum       = dma

        ch = self._ws.channel[channel]
        ch.gpionum    = pin
        ch.count      = num
        ch.invert     = int(invert)
        ch.brightness = brightness
        ch.strip_type = strip_type if strip_type is not None else WS2812_STRIP

    def begin(self):
        """Initialize the strip hardware. Raises RuntimeError on failure."""
        result = _lib.ws2811_init(ctypes.byref(self._ws))
        if result != WS2811_SUCCESS:
            raise RuntimeError(f'ws2811_init failed with code {result}')

    def show(self):
        """Push pixel data to the strip."""
        result = _lib.ws2811_render(ctypes.byref(self._ws))
        if result != WS2811_SUCCESS:
            raise RuntimeError(f'ws2811_render failed with code {result}')

    def setPixelColor(self, n, color):
        """Set pixel n to a packed Color value."""
        if 0 <= n < self._num:
            self._ws.channel[self._channel].leds[n] = color

    def setPixelColorRGB(self, n, red, green, blue, white=0):
        """Set pixel n to an r, g, b (w) color."""
        self.setPixelColor(n, Color(red, green, blue, white))

    def getBrightness(self):
        return self._ws.channel[self._channel].brightness

    def setBrightness(self, brightness):
        self._ws.channel[self._channel].brightness = brightness

    def getPixelColor(self, n):
        return self._ws.channel[self._channel].leds[n]

    def numPixels(self):
        return self._num

    def __del__(self):
        try:
            _lib.ws2811_fini(ctypes.byref(self._ws))
        except Exception:
            pass
