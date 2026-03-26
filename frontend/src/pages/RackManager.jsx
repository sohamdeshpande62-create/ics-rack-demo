import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { DndContext, PointerSensor, TouchSensor, useSensor, useSensors } from '@dnd-kit/core'
import Logo from '../components/shared/Logo.jsx'
import NodeBorder from '../components/shared/NodeBorder.jsx'
import StatusBanner from '../components/shared/StatusBanner.jsx'
import ItemCard from '../components/rack/ItemCard.jsx'
import RackView from '../components/rack/RackView.jsx'
import { createRack, updateLockStatus, createRow, createItem, updateItem } from '../api/client.js'
import { useItems } from '../hooks/useItems.js'
import { toAbsolute, toAbsoluteBottom, hasVisualOverlap, PLACE_LEDS } from '../utils/ledUtils.js'
import '../styles/rack.css'

const LABELS  = ['Pulse_Oximeter', 'EKG_Leads', 'Oxygen_Mask', 'Chest_Tube', 'Noise', 'Unknown']
const RACK_ID = 1

export default function RackManager() {
  const [stage, setStage] = useState(1)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  // Stage 1
  const [rackName, setRackName] = useState('')

  // Stage 2
  const [numRows,    setNumRows]    = useState('')
  const [ledsPerRow, setLedsPerRow] = useState('')
  const [rows,       setRows]       = useState([])

  // Stage 3
  const [itemName,      setItemName]      = useState('')
  const [itemLabel,     setItemLabel]     = useState(LABELS[0])
  const [itemRow,       setItemRow]       = useState('')
  const [stagingItems,  setStagingItems]  = useState([])
  const [pendingItems,  setPendingItems]  = useState([])

  const { items, refetch: refetchItems } = useItems(RACK_ID)

  // dnd-kit sensor: require 8px movement before drag activates (makes clicks still work)
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(TouchSensor,   { activationConstraint: { delay: 150, tolerance: 8 } })
  )

  // Remove from pending when item is confirmed in DB
  useEffect(() => {
    setPendingItems(prev =>
      prev.filter(p => {
        const confirmed = items.find(i => i.item_id === p.item_id)
        return !confirmed || (confirmed.led_start === 0 && confirmed.led_end === 0)
      })
    )
  }, [items])

  // ---- Stage 1: Create Rack ----
  const handleCreateRack = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await createRack(rackName.trim())
      await updateLockStatus(RACK_ID, true)
      setStage(2)
    } catch (err) {
      setError(err.message)
    }
  }

  // ---- Stage 2: Create Rows ----
  const handleCreateRows = async (e) => {
    e.preventDefault()
    setError('')
    const n    = parseInt(numRows)
    const leds = parseInt(ledsPerRow)
    if (isNaN(n) || n < 1 || n > 26) return setError('Number of rows must be 1–26')
    if (isNaN(leds) || leds < 1)      return setError('LEDs per row must be > 0')

    const created = []
    try {
      for (let i = 0; i < n; i++) {
        const row = await createRow(RACK_ID, leds, i * leds, i % 2 === 0 ? 'ltr' : 'rtl')
        created.push(row)
      }
      setRows(created)
      setItemRow(created[0]?.row_id || '')
      setStage(3)
    } catch (err) {
      setError(err.message)
    }
  }

  // ---- Stage 3: Create Item ----
  const handleCreateItem = async (e) => {
    e.preventDefault()
    setError('')
    if (!itemRow) return setError('Select a row')
    try {
      const item = await createItem(RACK_ID, itemRow, itemName.trim(), itemLabel)
      setStagingItems(prev => [...prev, item])
      setItemName('')
    } catch (err) {
      setError(err.message)
    }
  }

  // ---- Drag & Drop ----
  const handleDragEnd = ({ active, over }) => {
    if (!over) return
    const rowId = over.id.replace('row-', '')
    const row   = rows.find(r => r.row_id === rowId)
    if (!row) return

    const item = stagingItems.find(i => `card-${i.item_id}` === active.id)
      || items.find(i => `card-${i.item_id}` === active.id)
    if (!item) return

    // Place at center of row with default width, shift away from any overlaps
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

    setStagingItems(prev => prev.filter(i => i.item_id !== item.item_id))
    setPendingItems(prev => {
      const filtered = prev.filter(p => p.item_id !== item.item_id)
      return [...filtered, { ...item, row_id: rowId, _vStart: vS, _vEnd: vE }]
    })
  }

  const handleResize = (itemId, rowId, newVS, newVE) => {
    setPendingItems(prev =>
      prev.map(p => p.item_id === itemId ? { ...p, row_id: rowId, _vStart: newVS, _vEnd: newVE } : p)
    )
    // Re-enter pending if a confirmed item is resized
    const confirmed = items.find(i => i.item_id === itemId)
    if (confirmed && !(confirmed.led_start === 0 && confirmed.led_end === 0)) {
      setPendingItems(prev => {
        if (prev.find(p => p.item_id === itemId)) return prev
        return [...prev, { ...confirmed, row_id: rowId, _vStart: newVS, _vEnd: newVE }]
      })
    }
  }

  const handleConfirm = async (item, row, vStart, vEnd) => {
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
  }

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

  const rackFull = rows.length > 0 && rows.every(row => {
    const rowItems = items.filter(i => i.row_id === row.row_id && !(i.led_start === 0 && i.led_end === 0))
    const occupied = new Set()
    rowItems.forEach(item => {
      for (let l = item.led_start; l <= item.led_end; l++) occupied.add(l)
    })
    return occupied.size >= row.total_leds
  })

  if (saved) {
    return (
      <div className="page page--manager">
        <NodeBorder />
        <header className="page-header"><Logo /></header>
        <main className="save-success-screen">
          <div className="save-success-card">
            <span className="save-success-icon">✓</span>
            <h2>Rack saved</h2>
            <p>You can close this tab.</p>
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

            {/* Stage 1 */}
            <section className={`stage${stage === 1 ? ' stage--active' : ' stage--done'}`}>
              <h2 className="stage__title">
                <span className="stage__num">1</span> Rack Setup
              </h2>
              {stage === 1 ? (
                <form onSubmit={handleCreateRack} className="stage__form">
                  <label>
                    Rack Name
                    <input
                      type="text"
                      maxLength={20}
                      value={rackName}
                      onChange={e => setRackName(e.target.value)}
                      placeholder="e.g. Bay 1"
                      required
                    />
                  </label>
                  <button type="submit" className="btn btn--primary">Create Rack</button>
                </form>
              ) : (
                <p className="stage__summary">Rack: <strong>{rackName}</strong></p>
              )}
            </section>

            {/* Stage 2 */}
            <section className={`stage${stage === 2 ? ' stage--active' : stage > 2 ? ' stage--done' : ' stage--locked'}`}>
              <h2 className="stage__title">
                <span className="stage__num">2</span> Row Setup
              </h2>
              {stage === 2 ? (
                <form onSubmit={handleCreateRows} className="stage__form">
                  <label>
                    Number of rows (1–26)
                    <input type="number" min={1} max={26} value={numRows}
                      onChange={e => setNumRows(e.target.value)} required />
                  </label>
                  <label>
                    LEDs per row
                    <input type="number" min={1} value={ledsPerRow}
                      onChange={e => setLedsPerRow(e.target.value)} required />
                  </label>
                  <button type="submit" className="btn btn--primary">Create Rows</button>
                </form>
              ) : stage > 2 ? (
                <p className="stage__summary">{rows.length} rows, {ledsPerRow} LEDs each</p>
              ) : null}
            </section>

            {/* Stage 3 */}
            <section className={`stage${stage === 3 ? ' stage--active' : ' stage--locked'}`}>
              <h2 className="stage__title">
                <span className="stage__num">3</span> Add Items
              </h2>
              {stage === 3 && (
                <>
                  {rackFull && <p className="rack-full-warning">Rack is full — no LED space remaining</p>}
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
                        <ItemCard key={item.item_id} item={item} />
                      ))}
                    </div>
                  )}
                </>
              )}
            </section>

            {stage === 3 && (
              <button className="btn btn--exit" onClick={handleSaveExit}>
                Save &amp; Exit
              </button>
            )}
          </aside>

          {/* RIGHT PANEL */}
          <section className="right-panel">
            {rows.length === 0 ? (
              <div className="rack-empty-state">
                <p>Complete steps 1 &amp; 2 to see the rack grid</p>
              </div>
            ) : (
              <RackView
                rows={rows}
                items={items}
                pendingItems={pendingItems}
                onResize={handleResize}
                onConfirm={handleConfirm}
              />
            )}
          </section>
        </main>
      </div>
    </DndContext>
  )
}
