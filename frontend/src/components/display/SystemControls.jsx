import { useState } from 'react'
import { rebootSystem } from '../../api/client.js'

export default function SystemControls() {
  const [confirming, setConfirming] = useState(false)
  const [rebooting, setRebooting] = useState(false)

  const handleReboot = async () => {
    setRebooting(true)
    try {
      await rebootSystem()
    } catch {
      // Pi will drop connection immediately — this is expected
    }
  }

  if (rebooting) {
    return <div className="system-controls"><p className="rebooting-msg">Rebooting...</p></div>
  }

  return (
    <div className="system-controls">
      {!confirming ? (
        <button className="btn btn--danger" onClick={() => setConfirming(true)}>
          Reboot Pi
        </button>
      ) : (
        <div className="confirm-reboot">
          <p>Reboot the Pi?</p>
          <div className="confirm-reboot__actions">
            <button className="btn btn--danger" onClick={handleReboot}>Yes, reboot</button>
            <button className="btn btn--secondary" onClick={() => setConfirming(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  )
}
