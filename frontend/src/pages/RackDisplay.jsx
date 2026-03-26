import { useEffect, useState, useRef } from 'react'
import Logo from '../components/shared/Logo.jsx'
import NodeBorder from '../components/shared/NodeBorder.jsx'
import QRCode from '../components/display/QRCode.jsx'
import StatusPanel from '../components/display/StatusPanel.jsx'
import SystemControls from '../components/display/SystemControls.jsx'
import { getLastDetected } from '../api/client.js'
import '../styles/display.css'

const RACK_ID        = 1
const FADE_TIMEOUT_MS = 10000
const POLL_MS        = 2000

export default function RackDisplay() {
  const [lastItem,  setLastItem]  = useState(null)  // { item_id, item_name, item_label }
  const [faded,     setFaded]     = useState(false)
  const fadeTimer = useRef(null)

  useEffect(() => {
    let lastSeenId = null

    const poll = async () => {
      try {
        const detected = await getLastDetected(RACK_ID)

        // Only update when a genuinely new item is detected
        if (detected?.item_id && detected.item_id !== lastSeenId) {
          lastSeenId = detected.item_id
          setLastItem(detected)
          setFaded(false)

          if (fadeTimer.current) clearTimeout(fadeTimer.current)
          fadeTimer.current = setTimeout(() => setFaded(true), FADE_TIMEOUT_MS)
        }
      } catch {
        // API unavailable — keep showing last known state
      }
    }

    poll()
    const interval = setInterval(poll, POLL_MS)

    return () => {
      clearInterval(interval)
      if (fadeTimer.current) clearTimeout(fadeTimer.current)
    }
  }, [])

  return (
    <div className="page page--display">
      <NodeBorder />
      <header className="page-header">
        <Logo />
      </header>

      <main className="display-body">
        {/* Left 60%: QR Code */}
        <section className="display-left">
          <QRCode />
        </section>

        {/* Right 40%: Status stack */}
        <section className="display-right">
          <StatusPanel rackId={RACK_ID} />

          <div className={`active-item-panel${faded ? ' active-item-panel--faded' : ''}`}>
            <p className="active-item-panel__label">Last Detected</p>
            {lastItem && !faded ? (
              <div className="active-item-panel__content">
                <p className="active-item-panel__name">{lastItem.item_name}</p>
                <p className="active-item-panel__sub">{lastItem.item_label}</p>
              </div>
            ) : (
              <div className="listening">
                <span className="listening-dot" />
                <span>Listening...</span>
              </div>
            )}
          </div>

          <SystemControls />
        </section>
      </main>
    </div>
  )
}
