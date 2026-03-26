# system.py -- Soham Deshpande, Intelligent Clinical Systems Inc. 2026
# System-level endpoints (reboot, restart-api, etc.)

import asyncio
import os
import signal
import subprocess
from fastapi import APIRouter

router = APIRouter()


@router.post('/reboot', status_code=200)
async def reboot_system():
    """Reboots the Raspberry Pi. Requires passwordless sudo for reboot."""
    subprocess.Popen(['sudo', 'reboot'])
    return {'message': 'Rebooting...'}


@router.post('/restart', status_code=200)
async def restart_api():
    """
    Gracefully exits the API process so run.sh auto-restarts it.
    Use after Save & Exit to get a clean pipeline restart.
    """
    async def _exit():
        await asyncio.sleep(0.3)   # Give the HTTP response time to send
        os.kill(os.getpid(), signal.SIGTERM)
    asyncio.create_task(_exit())
    return {'message': 'Restarting API...'}
