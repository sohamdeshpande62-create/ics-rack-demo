# ICS Rack Demo — Claude Context

## Project Overview
Voice-activated medical supply rack demo. A Raspberry Pi 5 runs a FastAPI backend with Edge Impulse ML inference, controls WS2812B LED strips, and serves a React frontend. An iPad connects via WiFi hotspot, scans a QR code, and opens the rack management UI.

## Stack
- **Backend**: FastAPI + SQLAlchemy async + SQLite (`backend/main/database_manager.py` is the entry point)
- **Frontend**: React + Vite + dnd-kit drag-and-drop (`frontend/`)
- **Inference**: Edge Impulse `.eim` model via `edge_impulse_linux`
- **LEDs**: WS2812B strips via custom ctypes wrapper around `libws2811.so` (Pi5 branch)
- **Hardware**: Raspberry Pi 5, GPIO 18 for LED data, USB microphone

## Running the API
```bash
cd ~/ics-rack-demo
sudo -E .venv/bin/uvicorn backend.main.database_manager:database_manager --host 0.0.0.0 --port 8000 --reload
```
Must run as root for LED hardware access.

## Key Architecture Decisions

### Lock Status Semantics
`rack.locked = False` → rack is in **running/display mode** (pipeline runs)
`rack.locked = True` → rack is **locked for editing** (pipeline pauses)
This is counterintuitive — do not reverse it.

### Pipeline Flow
1. `pipeline_event` fires when first rack is created (`POST /racks`)
2. Pipeline checks lock status — runs if unlocked, waits if locked
3. Audio captured in 1-second windows → Edge Impulse classification
4. On detection above confidence threshold → query DB for active items with that label → light LEDs
5. LEDs auto-clear after `LED_TIMEOUT` seconds

### LED Architecture (Pi5)
The standard `rpi_ws281x` PyPI package does not support Pi5. The solution:
1. Pi5 branch of rpi_ws281x built from source at `~/rpi_ws281x_pi5/`
2. Shared library: `/usr/local/lib/libws2811.so` (built with `-DBUILD_SHARED=ON`)
3. Python ctypes wrapper: `backend/led/rpi_ws281x_compat.py` installed as `/usr/lib/python3/dist-packages/rpi_ws281x.py` AND `.venv/lib/python3.13/site-packages/rpi_ws281x.py`
4. Pi5 board revision `0xd04171` was manually added to `rpihw.c` (original only had `0xd04170`)
5. dtoverlay `rp1_ws281x_pwm` in `/boot/firmware/config.txt` creates the platform device — without it the kernel module loads but never probes
6. `gpio-ws281x.service` runs `pinctrl set 18 a3 pn` at boot (dtoverlay alone doesn't set GPIO alt function)

### Dual-Strip LED Lighting
Items light both top and bottom divider strips simultaneously. The pipeline calls `light_item()` for each active item. `clear_first=True` is passed only on the first item per detection to avoid clearing the first strip before the second is set.

### Frontend Network Access
- Vite runs with `--host` flag for network access from iPad
- `frontend/.env` (gitignored, Pi only): `VITE_API_BASE_URL=http://192.168.4.1:8000`
- iPad connects to Pi's hotspot at `192.168.4.1`

## Boot Persistence Setup (Pi)
All of these must be in place for full boot persistence:

| Component | Mechanism |
|-----------|-----------|
| LED kernel module | `dtoverlay=rp1_ws281x_pwm` in `/boot/firmware/config.txt` |
| GPIO 18 PWM mode | `gpio-ws281x.service` → `pinctrl set 18 a3 pn` |
| libws2811.so | `/usr/local/lib/libws2811.so` + `ldconfig` |
| Python wrapper | Installed in both system Python and venv site-packages |
| API service | `ics-api.service` enabled, runs as root |
| Frontend service | `ics-frontend.service` enabled |
| Kiosk display | `~/.config/labwc/autostart` → `launch-display.sh` |
| Screen rotation | `wlr-randr --output HDMI-A-1 --transform 180` in autostart |
| WiFi hotspot | NetworkManager AP connection (nmcli) |

## Common Commands

```bash
# Check all services
sudo systemctl status ics-api ics-frontend gpio-ws281x

# Watch live pipeline logs
sudo journalctl -u ics-api -f | grep -i "LED\|Pipeline\|Detected"

# Test LEDs directly
sudo python3 -c "
from rpi_ws281x import PixelStrip, Color
strip = PixelStrip(180, 18, 800000, 10, False, 255, 0)
strip.begin()
for i in range(180): strip.setPixelColor(i, Color(0, 50, 0))
strip.show()
"

# Check GPIO pin mode (should show a3)
pinctrl get 18

# Check LED device exists
ls /dev/ws281x_pwm

# Reset database
sudo systemctl stop ics-api
rm ~/ics-rack-demo/ics_rack.db
sudo systemctl start ics-api
```

## Pi5 LED Troubleshooting

**`/dev/ws281x_pwm` missing after reboot**
→ Check `dtoverlay=rp1_ws281x_pwm` is in `/boot/firmware/config.txt`
→ Module loads but doesn't probe without the overlay

**`ws2811_init failed: Hardware revision not supported`**
→ Check `/usr/local/lib/libws2811.so` exists and was built from pi5 branch with `0xd04171` in `rpihw.c`
→ Check `.venv` has our `rpi_ws281x.py` not the PyPI version (`sudo pip uninstall rpi-ws281x-python` in venv)

**LEDs don't light despite successful init**
→ Run `pinctrl get 18` — must show `a3`, not `ip` or `none`
→ Check `gpio-ws281x.service` is active: `sudo systemctl status gpio-ws281x`

**Module loads too early (before RP1 firmware)**
→ Do NOT use `/etc/modules-load.d/` for this module — it loads before RP1 is ready
→ Use dtoverlay in `config.txt` instead (loads at correct time via device tree)

## Important Files (Pi only, not in repo)
- `~/ics-rack-demo/.env` — environment variables including `LED_TOTAL`, `MIC_INDEX`
- `/boot/firmware/config.txt` — dtoverlay and display rotation
- `~/.config/labwc/autostart` — kiosk and rotation on boot
- `/etc/systemd/system/gpio-ws281x.service` — GPIO setup service
- `/usr/local/lib/libws2811.so` — compiled Pi5 LED library
- `~/rpi_ws281x_pi5/` — Pi5 branch source (keep — needed if kernel updates)

## Git Branch
Active development branch: `claude/gallant-bardeen`
Main branch: `main`
To pull specific files from dev branch on Pi:
```bash
git fetch origin
git checkout origin/claude/gallant-bardeen -- path/to/file
```
