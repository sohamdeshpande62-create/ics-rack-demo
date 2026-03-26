export default function StatusBanner({ message, type = 'info' }) {
  if (!message) return null
  return (
    <div className={`status-banner status-banner--${type}`}>
      {message}
    </div>
  )
}
