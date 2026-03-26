# events.py -- Soham Deshpande, Intelligent Clinical Systems Inc.


import asyncio

pipeline_event = asyncio.Event()

# In-memory last-detected state — updated by inference pipeline, read by /racks/{id}/last-detected
last_detected: dict = {
    'item_id':    None,
    'item_name':  None,
    'item_label': None,
}