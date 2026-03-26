import { useRef, useCallback } from 'react'
import { useDroppable } from '@dnd-kit/core'
import RowLabel from './RowLabel.jsx'
import { toVisual, hasVisualOverlap, LED_PX } from '../../utils/ledUtils.js'

// Visual representation of a physical LED divider strip (shelf edge)
function DividerStrip({ totalLeds }) {
  return (
    <div className="divider-strip">
      <div className="divider-label-spacer" />
      <div className="divider-leds" style={{ width: totalLeds * LED_PX }}>
        {Array.from({ length: totalLeds }, (_, i) => (
          <div key={i} className="led-dot led-dot--divider" />
        ))}
      </div>
    </div>
  )
}

const ICS_BLUE = 'rgb(58, 103, 176)'
const LED_RED  = '#e53e3e'

// Single row drop zone with LED dots and placed/pending item overlays
function RowBand({ row, placedItems, pendingItems, onResize, onConfirm, onUnplace, allRows }) {
  const { setNodeRef, isOver } = useDroppable({ id: `row-${row.row_id}` })
  const bandRef = useRef(null)

  const placed  = placedItems.filter(i => i.row_id === row.row_id)
  const pending = pendingItems.filter(i => i.row_id === row.row_id)

  // Build set of occupied visual positions for dot colouring
  const occupiedVis = new Set()
  placed.forEach(item => {
    const vS = toVisual(item.led_start, row)
    const vE = toVisual(item.led_end, row)
    for (let v = Math.min(vS, vE); v <= Math.max(vS, vE); v++) occupiedVis.add(v)
  })
  pending.forEach(item => {
    if (item._vStart !== undefined) {
      for (let v = Math.min(item._vStart, item._vEnd); v <= Math.max(item._vStart, item._vEnd); v++) {
        occupiedVis.add(v)
      }
    }
  })

  return (
    <div className="row-band">
      <RowLabel rowId={row.row_id} />
      <div
        ref={(el) => { setNodeRef(el); bandRef.current = el }}
        className={`row-leds${isOver ? ' row-leds--over' : ''}`}
        style={{ width: row.total_leds * LED_PX }}
        data-row-id={row.row_id}
      >
        {/* LED dots */}
        {Array.from({ length: row.total_leds }, (_, vi) => (
          <div
            key={vi}
            className="led-dot"
            style={{ backgroundColor: occupiedVis.has(vi) ? ICS_BLUE : LED_RED }}
          />
        ))}

        {/* Confirmed placed items */}
        {placed.map(item => {
          const vS = toVisual(item.led_start, row)
          const vE = toVisual(item.led_end, row)
          const lo = Math.min(vS, vE)
          const hi = Math.max(vS, vE)
          return (
            <PlacedItem
              key={item.item_id}
              item={item}
              vStart={lo}
              vEnd={hi}
              row={row}
              confirmed={true}
              allItems={placedItems}
              allRows={allRows}
              onResize={onResize}
              onConfirm={onConfirm}
              onUnplace={onUnplace}
            />
          )
        })}

        {/* Pending (dragged, not yet confirmed) items */}
        {pending.map(item => {
          if (item._vStart === undefined) return null
          const lo = Math.min(item._vStart, item._vEnd)
          const hi = Math.max(item._vStart, item._vEnd)
          return (
            <PlacedItem
              key={item.item_id}
              item={item}
              vStart={lo}
              vEnd={hi}
              row={row}
              confirmed={false}
              allItems={placedItems}
              allRows={allRows}
              onResize={onResize}
              onConfirm={onConfirm}
              onUnplace={onUnplace}
            />
          )
        })}
      </div>
    </div>
  )
}

function PlacedItem({ item, vStart, vEnd, row, confirmed, allItems, allRows, onResize, onConfirm, onUnplace }) {
  const left  = vStart * LED_PX
  const width = (vEnd - vStart + 1) * LED_PX

  const handleResizeStart = useCallback((e, side) => {
    e.preventDefault()
    e.stopPropagation()
    const startX     = e.clientX
    const startVStart = vStart
    const startVEnd   = vEnd

    const onMove = (me) => {
      const dLeds = Math.round((me.clientX - startX) / LED_PX)
      let newVS = startVStart
      let newVE = startVEnd

      if (side === 'left') {
        newVS = Math.max(0, Math.min(startVStart + dLeds, startVEnd))
      } else {
        newVE = Math.min(row.total_leds - 1, Math.max(startVEnd + dLeds, startVStart))
      }

      if (!hasVisualOverlap(newVS, newVE, row.row_id, allItems, item.item_id, allRows)) {
        onResize(item.item_id, row.row_id, newVS, newVE)
      }
    }

    const onUp = () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }

    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }, [vStart, vEnd, row, allItems, allRows, item, onResize])

  return (
    <div
      className={`placed-item${confirmed ? ' placed-item--confirmed' : ' placed-item--pending'}`}
      style={{ left, width }}
    >
      <div className="resize-handle resize-handle--left"  onMouseDown={e => handleResizeStart(e, 'left')} />
      <span className="placed-item__name">{item.name}</span>
      {!confirmed && (
        <button className="confirm-btn" onClick={() => onConfirm(item, row, vStart, vEnd)}>
          Confirm
        </button>
      )}
      {confirmed && onUnplace && (
        <button className="unplace-btn" onClick={() => onUnplace(item)}>
          Move
        </button>
      )}
      <div className="resize-handle resize-handle--right" onMouseDown={e => handleResizeStart(e, 'right')} />
    </div>
  )
}

// RackView is now a pure display component.
// DndContext lives in the parent (RackManager / RackEditor) so that
// draggable ItemCards in the left panel share the same drag context
// as these droppable row bands.
export default function RackView({ rows, items, pendingItems, onResize, onConfirm, onUnplace }) {
  const placedItems = items.filter(i => !(i.led_start === 0 && i.led_end === 0))

  return (
    <div className="rack-view">
      {rows.map(row => (
        // Each row is sandwiched: DividerStrip (top) → RowBand → DividerStrip (bottom of last row added after loop)
        // We render a top divider before every row; the final bottom divider comes after the last row.
        <div key={row.row_id}>
          <DividerStrip totalLeds={row.total_leds} />
          <RowBand
            row={row}
            placedItems={placedItems}
            pendingItems={pendingItems}
            onResize={onResize}
            onConfirm={onConfirm}
            onUnplace={onUnplace}
            allRows={rows}
          />
        </div>
      ))}
      {/* Bottom divider of the last row */}
      {rows.length > 0 && <DividerStrip totalLeds={rows[rows.length - 1].total_leds} />}
    </div>
  )
}
