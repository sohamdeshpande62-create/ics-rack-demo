const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== null) opts.body = JSON.stringify(body)
  const res = await fetch(`${BASE_URL}${path}`, opts)
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(detail.detail || res.statusText)
  }
  return res.json()
}

// Racks
export const createRack = (name) =>
  request('POST', '/racks', { name, locked: false })

export const getLockStatus = (rackId) =>
  request('GET', `/racks/${rackId}/lock-status`)

export const updateLockStatus = (rackId, locked) =>
  request('PUT', `/racks/${rackId}/update-lock-status?locked=${locked}`)

// Rows
export const createRow = (rackId, totalLeds, ledOffset, direction) =>
  request('POST', '/rows', { rack_id: rackId, total_leds: totalLeds, led_offset: ledOffset, direction })

export const getRows = (rackId) =>
  request('GET', `/rows/rack/${rackId}`)

// Items
export const createItem = (rackId, rowId, name, label) =>
  request('POST', '/items', { rack_id: rackId, row_id: rowId, name, label, led_start: 0, led_end: 0 })

export const getAllItems = (rackId) =>
  request('GET', `/items/rack/${rackId}`)

export const updateItem = (itemId, { rowId, ledStart, ledEnd, ledStartB, ledEndB, isActive }) =>
  request('PUT', `/items/${itemId}`, {
    row_id:      rowId,
    led_start:   ledStart,
    led_end:     ledEnd,
    led_start_b: ledStartB,
    led_end_b:   ledEndB,
    is_active:   isActive,
  })

export const deleteItem = (itemId) =>
  request('DELETE', `/items/${itemId}`)

// System
export const rebootSystem = () =>
  request('POST', '/system/reboot')

export const restartApi = () =>
  request('POST', '/system/restart')

// Display
export const getLastDetected = (rackId) =>
  request('GET', `/racks/${rackId}/last-detected`)
