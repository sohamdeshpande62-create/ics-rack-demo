// RackEditor.jsx — loaded when iPad scans the QR code.
// Skips rack/row creation (already configured on Pi) and goes straight
// to item editing: add new items, reposition, resize, or delete.

import { useState, useEffect, useCallback } from 'react'
import { DndContext, PointerSensor, useSensor, useSensors } from '@dnd-kit/core'
import Logo from '../components/shared/Logo.jsx'
import NodeBorder from '../components/shared/NodeBorder.jsx'
import StatusBanner from '../components/shared/StatusBanner.jsx'
import ItemCard from '../components/rack/ItemCard.jsx'
import RackView from '../components/rack/RackView.jsx'
import { useNavigate } from 'react-router-dom'
import { updateLockStatus, getRows, createItem, updateItem, deleteItem } from '../api/client.js'
import { useItems } from '../hooks/useItems.js'
import { toAbsolute, toAbsoluteBottom, hasVisualOverlap, PLACE_LEDS } from '../utils/ledUtils.js'
import '../styles/rack.css'

const LABELS  = ['Pulse_Oximeter', 'EKG_Leads', 'Oxygen_Mask', 'Chest_Tube', 'Noise', 'Unknown']
const RACK_ID = 1

export default function RackEditor() {
  const navigate = useNavigate()
  const [rows,         setRows]         = useState([])
  const [loading,      setLoading]      = useState(true)
  const [noRack,       setNoRack]       = useState(false)
  const [error,        setError]        = useState('')
  const [saved,        setSaved]        = useState(false)
  const [pendingItems, setPendingItems] = useState([])

  // Item creation form state
  const [itemName,  setItemName]  = useState('')
  const [itemLabel, setItemLabel] = useState(LABELS[0])
  const [itemRow,   setItemRow]   = useState('')

  const { items, refetch: refetchItems } = useItems(RACK_ID)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  )

  // On mount: load rows and lock the rack for editing
  useEffect(() => {
    async function init() {
      try {
        const loadedRows = await getRows(RACK_ID)
        if (!loadedRows || loadedRows.length === 0) {
          setNoRack(true)
          return
        }
        setRows(loadedRows)
        setItemRow(loadedRows[0].row_id)
        await updateLockStatus(RACK_ID, true)
      } catch (e) {
        // 404 = rack not yet set up on the Pi
        if (e.message?.includes('404') || e.message?.toLowerCase().includes('not found')) {
          setNoRack(true)
        } else {
          setError(`Could not load rack: ${e.message}`)
        }
      } finally {
        setLoading(false)
      }
    }
    init()

    // Unlock on unmount (e.g. tab close — best-effort)
    return () => { updateLockStatus(RACK_ID, false).catch(() => {}) }
  }, [])

  // Remove from pending once item is confirmed in DB
  useEffect(() => {
    setPendingItems(prev =>
      prev.filter(p => {
        const confirmed = items.find(i => i.item_id === p.item_id)
        return !confirmed || (confirmed.led_start === 0 && confirmed.led_end === 0)
      })
    )
  }, [items])

  // Staging = DB items with no position assigned, minus anything currently pending
  const pendingIds   = new Set(pendingItems.map(p => p.item_id))
  const stagingItems = items.filter(i => i.led_start === 0 && i.led_end === 0 && !pendingIds.has(i.item_id))

  // ---- Create Item ----
  const handleCreateItem = async (e) => {
    e.preventDefault()
    setError('')
    if (!itemRow) return setError('Select a row')
    try {
      await createItem(RACK_ID, itemRow, itemName.trim(), itemLabel)
      refetchItems()
      setItemName('')
    } catch (err) {
      setError(err.message)
    }
  }

  // ---- Drag & Drop ----
  const handleDragEnd = useCallback(({ active, over }) => {
    if (!over) return
    const rowId = over.id.replace('row-', '')
    const row   = rows.find(r => r.row_id === rowId)
    if (!row) return

    const item = stagingItems.find(i => `card-${i.item_id}` === active.id)
      || items.find(i => `card-${i.item_id}` === active.id)
    if (!item) return

    const centerV = Math.floor(row.total_leds / 2)
    const half    = Math.floor(PLACE_LEDS / 2)
    let vS = Math.max(0, centerV - half)
    let vE = Math.min(row.total_leds - 1, vS + PLACE_LEDS - 1)

    const allForOverlap = [...items, ...pendingItems]
    let attempts = 0
    while (hasVisualOverlap(vS, vE, rowId, allForOverlap, item.item_id, rows) && attempts < row.total_leds) {
      vS = Math.min(vS + 1, row.total_leds - PLACE_LEDS)
      vE = vS + PLACE_LEDS - 1
      attempts++
    }
    if (vE >= row.total_leds) {
      vE = row.total_leds - 1
      vS = Math.max(0, vE - PLACE_LEDS + 1)
    }

    setPendingItems(prev => {
      const filtered = prev.filter(p => p.item_id !== item.item_id)
      return [...filtered, { ...item, row_id: rowId, _vStart: vS, _vEnd: vE }]
    })
  }, [rows, items, stagingItems, pendingItems])

  const handleResize = useCallback((itemId, rowId, newVS, newVE) => {
    setPendingItems(prev =>
      prev.map(p => p.item_id === itemId ? { ...p, row_id: rowId, _vStart: newVS, _vEnd: newVE } : p)
    )
    const confirmed = items.find(i => i.item_id === itemId)
    if (confirmed && !(confirmed.led_start === 0 && confirmed.led_end === 0)) {
      setPendingItems(prev => {
        if (prev.find(p => p.item_id === itemId)) return prev
        return [...prev, { ...confirmed, row_id: rowId, _vStart: newVS, _vEnd: newVE }]
      })
    }
  }, [items])

  const handleConfirm = useCallback(async (item, row, vStart, vEnd) => {
    const absStart  = toAbsolute(vStart, row)
    const absEnd    = toAbsolute(vEnd,   row)
    const ledStart  = Math.min(absStart, absEnd)
    const ledEnd    = Math.max(absStart, absEnd)

    const absStartB = toAbsoluteBottom(vStart, row)
    const absEndB   = toAbsoluteBottom(vEnd,   row)
    const ledStartB = Math.min(absStartB, absEndB)
    const ledEndB   = Math.max(absStartB, absEndB)

    try {
      await updateItem(item.item_id, { rowId: row.row_id, ledStart, ledEnd, ledStartB, ledEndB })
      setPendingItems(prev => prev.filter(p => p.item_id !== item.item_id))
      refetchItems()
    } catch (e) {
      setError(`Could not confirm placement: ${e.message}`)
    }
  }, [refetchItems])

  // Toggle is_active without moving the item
  const handleToggleActive = useCallback(async (item) => {
    try {
      await updateItem(item.item_id, { isActive: !item.is_active })
      refetchItems()
    } catch (e) {
      setError(`Could not update item: ${e.message}`)
    }
  }, [refetchItems])

  // Unplace: send item back to staging (zero out both strips)
  const handleUnplace = useCallback(async (item) => {
    try {
      await updateItem(item.item_id, { rowId: item.row_id, ledStart: 0, ledEnd: 0, ledStartB: 0, ledEndB: 0 })
      refetchItems()
    } catch (e) {
      setError(`Could not unplace item: ${e.message}`)
    }
  }, [refetchItems])

  // Delete item entirely
  const handleDelete = useCallback(async (item) => {
    try {
      await deleteItem(item.item_id)
      refetchItems()
    } catch (e) {
      setError(`Could not delete item: ${e.message}`)
    }
  }, [refetchItems])

  // ---- Save & Exit ----
  // Unlock the rack — the running pipeline wakes up automatically, no restart needed
  const handleSaveExit = async () => {
    setError('')
    try {
      await updateLockStatus(RACK_ID, false)
      setSaved(true)
    } catch (err) {
      setError(err.message)
    }
  }

  // ---- Render states ----
  if (loading) {
    return (
      <div className="page page--manager">
        <NodeBorder />
        <header className="page-header"><Logo /></header>
        <main className="save-success-screen">
          <p style={{ color: '#aaa' }}>Loading rack…</p>
        </main>
      </div>
    )
  }

  if (noRack) {
    return (
      <div className="page page--manager">
        <NodeBorder />
        <header className="page-header"><Logo /></header>
        <main className="save-success-screen">
          <div className="save-success-card">
            <span className="save-success-icon" style={{ color: '#e53e3e' }}>!</span>
            <h2>No rack configured</h2>
            <p>No rack has been set up yet.</p>
            <button className="btn btn--primary" style={{ marginTop: 16 }} onClick={() => navigate('/')}>
              Create New Rack
            </button>
          </div>
        </main>
      </div>
    )
  }

  if (saved) {
    return (
      <div className="page page--manager">
        <NodeBorder />
        <header className="page-header"><Logo /></header>
        <main className="save-success-screen">
          <div className="save-success-card">
            <span className="save-success-icon">✓</span>
            <h2>Changes saved</h2>
            <p>You can close this tab.</p>
            <button className="btn btn--primary" style={{ marginTop: 16 }} onClick={() => navigate('/')}>
              Create New Rack
            </button>
          </div>
        </main>
      </div>
    )
  }

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="page page--manager">
        <NodeBorder />
        <header className="page-header"><Logo /></header>

        <main className="manager-body">
          {/* LEFT PANEL */}
          <aside className="left-panel">
            {error && <StatusBanner message={error} type="error" />}

            <section className="stage stage--active">
              <h2 className="stage__title">Edit Items</h2>

              <form onSubmit={handleCreateItem} className="stage__form">
                <label>
                  Name
                  <input type="text" maxLength={30} value={itemName}
                    onChange={e => setItemName(e.target.value)}
                    placeholder="e.g. Pulse Oximeter" required />
                </label>
                <label>
                  Label
                  <select value={itemLabel} onChange={e => setItemLabel(e.target.value)}>
                    {LABELS.map(l => <option key={l} value={l}>{l}</option>)}
                  </select>
                </label>
                <label>
                  Row
                  <select value={itemRow} onChange={e => setItemRow(e.target.value)}>
                    {rows.map(r => <option key={r.row_id} value={r.row_id}>{r.row_id}</option>)}
                  </select>
                </label>
                <button type="submit" className="btn btn--primary">Add Item</button>
              </form>

              {stagingItems.length > 0 && (
                <div className="staging-area">
                  <p className="staging-area__label">Drag items onto the rack →</p>
                  {stagingItems.map(item => (
                    <div key={item.item_id} className="staging-item-row">
                      <ItemCard item={item} />
                      <button
                        className="btn btn--danger-sm"
                        onClick={() => handleDelete(item)}
                        title="Delete item"
                      >✕</button>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <button className="btn btn--exit" onClick={handleSaveExit}>
              Save &amp; Exit
            </button>
          </aside>

          {/* RIGHT PANEL */}
          <section className="right-panel">
            <RackView
              rows={rows}
              items={items}
              pendingItems={pendingItems}
              onResize={handleResize}
              onConfirm={handleConfirm}
              onUnplace={handleUnplace}
              onToggleActive={handleToggleActive}
            />
          </section>
        </main>
      </div>
    </DndContext>
  )
}
