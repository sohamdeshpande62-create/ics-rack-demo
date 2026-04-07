# ICS Rack Demo

A voice-activated medical supply rack management system built by Intelligent Clinical Systems Inc. The system uses a Raspberry Pi 5 to run real-time audio classification, control WS2812B LED strips, and serve a touch-friendly React UI. An iPad connects via a local WiFi hotspot to manage rack configuration while the Pi drives a kiosk display.

---

## System Overview

```
┌─────────────────────────────────────────────────────┐
│                  Raspberry Pi 5                     │
│                                                     │
│  ┌─────────────┐   ┌──────────────┐                │
│  │  FastAPI    │   │  React/Vite  │                │
│  │  Backend    │   │  Frontend    │                │
│  │  :8000      │   │  :5173       │                │
│  └──────┬──────┘   └──────┬───────┘                │
│         │                 │                         │
│  ┌──────▼──────────────────▼───────┐               │
│  │      Inference Pipeline         │               │
│  │  Mic → Edge Impulse → LED ctrl  │               │
│  └─────────────────────────────────┘               │
│                                                     │
│  GPIO 18 ──────────────────────► WS2812B LEDs      │
│  WiFi Hotspot (192.168.4.1) ───► iPad / Browser    │
└─────────────────────────────────────────────────────┘
```

**Workflow:**
1. iPad connects to Pi's WiFi hotspot and opens the rack editor via QR code
2. Clinician configures the rack — rows, items, LED ranges, and AI labels
3. Rack goes into running mode; Pi listens continuously via USB microphone
4. Clinician says an item name (e.g., "Pulse Oximeter")
5. Edge Impulse model classifies the audio and triggers the corresponding LED range
6. LEDs auto-clear after 10 seconds or immediately when a new item is called

---

## Hardware Requirements

| Component | Details |
|-----------|---------|
| Raspberry Pi 5 | 4GB or 8GB RAM |
| WS2812B LED strips | Daisy-chained, data on GPIO 18 (physical pin 12) |
| USB microphone | Any USB mic; set `MIC_INDEX` in `.env` |
| 5V power supply | For LED strips (external, shared ground with Pi) |
| Display | HDMI touchscreen (Hosyond 7" or similar) |
| WiFi | Pi's built-in WiFi used as hotspot |

---

## Software Architecture

### Backend (`/backend`)
- **FastAPI** async REST API with SQLAlchemy + SQLite
- **Inference pipeline**: continuous audio capture → Edge Impulse classification → LED control
- **LED control**: ctypes wrapper around `libws2811.so` (custom Pi5 build)

### Frontend (`/frontend`)
- **React + Vite** single-page app
- **dnd-kit** drag-and-drop for item placement
- **Three views**: rack setup, iPad editor, kiosk display

### Key Files

```
ics-rack-demo/
├── backend/
│   ├── core/config.py              # Environment variable loading
│   ├── crud/                       # DB operations (items, racks, rows)
│   ├── inference/
│   │   ├── audio_capture.py        # PyAudio mic input
│   │   └── inference_model.py      # Edge Impulse runner
│   ├── led/
│   │   ├── led_controller.py       # LED strip control
│   │   └── rpi_ws281x_compat.py    # Pi5 ctypes wrapper
│   ├── main/
│   │   ├── database_manager.py     # FastAPI app entry point
│   │   ├── inference_pipeline.py   # Main inference loop
│   │   ├── events.py               # Pipeline trigger event
│   │   └── models.py               # SQLAlchemy ORM models
│   ├── routers/                    # API route handlers
│   └── schemas/                    # Pydantic validation schemas
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── RackManager.jsx     # Rack/row creation
│       │   ├── RackEditor.jsx      # iPad item editor
│       │   └── RackDisplay.jsx     # Kiosk live display
│       ├── api/                    # HTTP client layer
│       └── utils/ledUtils.js       # LED index calculations
├── systemd/
│   ├── ics-api.service
│   └── ics-frontend.service
├── launch-display.sh               # Chromium kiosk launcher
├── .env.example                    # Environment variable template
└── CLAUDE.md                       # AI assistant context
```

---

## API Reference

**Base URL:** `http://192.168.4.1:8000`

### Racks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/racks` | Create a new rack |
| GET | `/racks/{id}/lock-status` | Get lock state (`true` = editing, `false` = running) |
| PUT | `/racks/{id}/update-lock-status?locked={bool}` | Set lock state |
| GET | `/racks/{id}/last-detected` | Get last detected item |

### Rows
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rows` | Create a row (row_id auto-assigned A, B, C...) |
| GET | `/rows/rack/{rack_id}` | Get all rows for a rack |

### Items
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/items` | Create an item |
| GET | `/items/rack/{rack_id}` | Get all items on a rack |
| PUT | `/items/{id}` | Update item (position, LED range, active status) |
| DELETE | `/items/{id}` | Delete item |

---

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# AI Model
MODEL_PATH='backend/inference/model/your_model.eim'

# Inference tuning
COOLDOWN_TIME=3.0        # Seconds before same item re-triggers
CONFIDENCE_LEVEL=0.85    # Minimum classification confidence

# Hardware
LED_PIN=18               # GPIO pin for LED data line
LED_TOTAL=180            # Total LEDs across all daisy-chained strips
MIC_INDEX=1              # PyAudio device index for USB microphone

# Server
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=sqlite:///./ics_rack.db
```

To find your microphone index:
```bash
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(i, p.get_device_info_by_index(i)['name']) for i in range(p.get_device_count())]"
```

---

## Pi Setup Guide

### 1. System Dependencies
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv nodejs npm chromium
```

### 2. Python Environment
```bash
cd ~/ics-rack-demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Frontend
```bash
cd frontend
npm install
```

### 4. WS2812B LED Support (Pi5)

The standard `rpi_ws281x` package does not support Pi5. You must build from the Pi5 branch:

```bash
# Clone Pi5 branch
git clone -b pi5 https://github.com/Drewsif/rpi_ws281x rpi_ws281x_pi5
cd rpi_ws281x_pi5

# Add your board revision to rpihw.c
# Find the 0xd04170 block and add an identical block with your revision
# Check your revision: cat /proc/cpuinfo | grep Revision
nano rpihw.c

# Build kernel module
cd rp1_ws281x_pwm
make
sudo cp rp1_ws281x_pwm.ko /lib/modules/$(uname -r)/
sudo depmod -a
# Install dtoverlay
sudo cp rp1_ws281x_pwm.dtbo /boot/firmware/overlays/
cd ..

# Build shared library
cmake -DBUILD_SHARED=ON .
make
sudo cp libws2811.so /usr/local/lib/libws2811.so
sudo ldconfig

# Install Python wrapper (from repo)
sudo cp ~/ics-rack-demo/backend/led/rpi_ws281x_compat.py /usr/lib/python3/dist-packages/rpi_ws281x.py
sudo cp ~/ics-rack-demo/backend/led/rpi_ws281x_compat.py ~/ics-rack-demo/.venv/lib/python3.13/site-packages/rpi_ws281x.py

# Uninstall the PyPI version if present (it takes precedence over our .py file)
sudo ~/ics-rack-demo/.venv/bin/pip uninstall rpi-ws281x-python
```

Add to `/boot/firmware/config.txt`:
```
dtoverlay=rp1_ws281x_pwm
```

### 5. GPIO Service (sets PWM alt function at boot)
```bash
sudo tee /etc/systemd/system/gpio-ws281x.service << 'EOF'
[Unit]
Description=Configure GPIO 18 for WS281x PWM
After=local-fs.target
Before=ics-api.service

[Service]
Type=oneshot
ExecStart=/usr/bin/pinctrl set 18 a3 pn
ExecStartPost=/sbin/udevadm trigger
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable gpio-ws281x
```

### 6. WiFi Hotspot
```bash
sudo nmcli device wifi hotspot ifname wlan0 ssid "ICS-Rack" password "yourpassword"
sudo nmcli connection modify "ICS-Rack Hotspot" connection.autoconnect yes
```

### 7. Systemd Services
```bash
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ics-api ics-frontend
sudo systemctl start ics-api ics-frontend
```

The API service must run as root for LED hardware access. Edit `ics-api.service` to set `User=root` and the correct venv path.

### 8. Kiosk Display (labwc/Wayland)
```bash
# Create autostart file
nano ~/.config/labwc/autostart
```

```bash
sleep 2 && wlr-randr --output HDMI-A-1 --transform 180 &
/home/ics/ics-rack-demo/launch-display.sh &
```

```bash
chmod +x ~/ics-rack-demo/launch-display.sh
```

### 9. Frontend Environment
Create `frontend/.env` (not committed — Pi specific):
```env
VITE_API_BASE_URL=http://192.168.4.1:8000
VITE_PI_IP=192.168.4.1
```

---

## Running Manually

```bash
# Terminal 1 — Backend
cd ~/ics-rack-demo
sudo -E .venv/bin/uvicorn backend.main.database_manager:database_manager \
    --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend
cd ~/ics-rack-demo/frontend
npm run dev
```

Access the UI at `http://192.168.4.1:5173` from the iPad.

---

## Monitoring

```bash
# Live pipeline logs — detections and LED events
sudo journalctl -u ics-api -f | grep -i "Detected\|LED\|Pipeline"

# All service status
sudo systemctl status ics-api ics-frontend gpio-ws281x

# Verify LED hardware
pinctrl get 18          # Should show a3 (PWM alt function)
ls /dev/ws281x_pwm      # Should exist
```

---

## Resetting the Database

```bash
sudo systemctl stop ics-api
rm ~/ics-rack-demo/ics_rack.db
sudo systemctl start ics-api
```

---

## LED Strip Wiring

```
Raspberry Pi 5          WS2812B Strip
─────────────           ─────────────
GPIO 18 (pin 12) ──────► Data In
GND      (pin 14) ──────► GND
                         VCC ◄────── External 5V PSU
                         GND ◄────── External 5V PSU GND
```

Multiple strips are daisy-chained: Data Out of strip N connects to Data In of strip N+1. All strips share common ground with the Pi.

---

## AI Model

The system uses an [Edge Impulse](https://edgeimpulse.com) audio classification model (`.eim` format) trained on voice commands for medical supply items. The model:
- Takes 1-second audio windows at 16kHz mono
- Outputs classification labels with confidence scores
- Filters out "Noise" and "Unknown" labels
- Requires confidence ≥ `CONFIDENCE_LEVEL` (default 0.85) to trigger LEDs

Place your model at the path specified by `MODEL_PATH` in `.env`.

---

## License

Copyright © 2026 Intelligent Clinical Systems Inc. All rights reserved.
