import { useEffect, useState } from 'react'
import { getLockStatus } from '../../api/client.js'

export default function StatusPanel({ rackId, rackName }) {
  const [locked, setLocked] = useState(null)

  useEffect(() => {
    const poll = async () => {
      try {
        const status = await getLockStatus(rackId)
        setLocked(status)
      } catch {
        // silently ignore polling errors
      }
    }
    poll()
    const interval = setInterval(poll, 3000)
    return () => clearInterval(interval)
  }, [rackId])

  return (
    <div className="status-panel">
      <h2 className="status-panel__name">{rackName || `Rack ${rackId}`}</h2>
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
