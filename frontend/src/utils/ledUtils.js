// LED position utility functions shared between RackManager and RackEditor

export const LED_PX = 20      // pixels per LED position
export const PLACE_LEDS = 5   // default width when an item is dropped

// Convert visual (left-to-right display) position to absolute LED index on top strip
export function toAbsolute(visualPos, row) {
  if (row.direction === 'ltr') {
    return row.led_offset + visualPos
  } else {
    return row.led_offset + (row.total_leds - 1 - visualPos)
  }
}

// Convert visual position to absolute LED index on the BOTTOM divider strip.
// The bottom strip is the next strip in the snake chain:
//   offset  = row.led_offset + row.total_leds
//   direction = opposite of row.direction (snake wiring)
export function toAbsoluteBottom(visualPos, row) {
  const bottomOffset = row.led_offset + row.total_leds
  if (row.direction === 'ltr') {
    // bottom runs rtl
    return bottomOffset + (row.total_leds - 1 - visualPos)
  } else {
    // bottom runs ltr
    return bottomOffset + visualPos
  }
}

// Convert absolute LED index to visual position
export function toVisual(absolute, row) {
  if (row.direction === 'ltr') {
    return absolute - row.led_offset
  } else {
    return row.led_offset + row.total_leds - 1 - absolute
  }
}

// Returns true if visual range [vStart, vEnd] overlaps any placed item on this row
export function hasVisualOverlap(vStart, vEnd, rowId, placedItems, excludeId, rows) {
  const row = rows.find(r => r.row_id === rowId)
  if (!row) return false
  return placedItems.some(item => {
    if (item.row_id !== rowId) return false
    if (item.item_id === excludeId) return false
    if (item.led_start === 0 && item.led_end === 0) return false // unplaced staging
    const iVStart = toVisual(item.led_start, row)
    const iVEnd = toVisual(item.led_end, row)
    const lo = Math.min(iVStart, iVEnd)
    const hi = Math.max(iVStart, iVEnd)
    return vEnd >= lo && vStart <= hi
  })
}
