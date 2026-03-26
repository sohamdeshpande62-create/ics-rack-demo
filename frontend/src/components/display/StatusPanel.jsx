import { useEffect, useState } from 'react'
import { getRack, getLockStatus } from '../../api/client.js'

export default function StatusPanel({ rackId }) {
  const [rackName, setRackName] = useState(null)   // null = loading, false = not found
  const [locked,   setLocked]   = useState(null)

  // Fetch rack name once on mount
  useEffect(() => {
    getRack(rackId)
      .then(r => setRackName(r.name))
      .catch(() => setRackName(false))
  }, [rackId])

  // Poll lock status
  useEffect(() => {
    const poll = async () => {
      try {
        setLocked(await getLockStatus(rackId))
      } catch {
        // silently ignore polling errors
      }
    }
    poll()
    const interval = setInterval(poll, 3000)
    return () => clearInterval(interval)
  }, [rackId])

  const displayName = rackName === null
    ? '…'
    : rackName === false
      ? 'Rack not set up'
      : rackName

  return (
    <div className="status-panel">
      <h2 className="status-panel__name">{displayName}</h2>
      <div className="status-panel__indicator">
        <span
          className="status-dot"
          style={{ backgroundColor: locked === false ? '#38a169' : '#e53e3e' }}
        />
        <span className="status-panel__label">
          {locked === null ? 'Connecting...' : locked ? 'Paused (locked)' : 'Running'}
        </span>
      </div>
    </div>
  )
}
