import { QRCodeSVG } from 'qrcode.react'

const PI_IP = import.meta.env.VITE_PI_IP || 'localhost'
const QR_URL = `http://${PI_IP}:5173/edit`

export default function QRCode() {
  return (
    <div className="qr-block">
      <QRCodeSVG value={QR_URL} size={280} bgColor="#ffffff" fgColor="#1a1a2e" />
      <p className="qr-label">Scan to manage this rack</p>
      <p className="qr-url">{QR_URL}</p>
    </div>
  )
}
