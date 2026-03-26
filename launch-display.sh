#!/bin/bash
# Wait for the frontend service to be ready before opening browser

until curl -s http://localhost:5173/ > /dev/null 2>&1; do
    sleep 1
done
chromium \
  --kiosk \
  --noerrdialogs \
  --disable-inforbars \
  --no-first-run \
  --disable-session-crashed-bubble \
  --password-store=basic \
  http://localhost:5173/display