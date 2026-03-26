export default function Logo() {
  return (
    <div className="logo-block">
      <img
        src="/ics-logo.png"
        alt="Intelligent Clinical Systems"
        className="logo-img"
        onError={(e) => { e.target.style.display = 'none' }}
      />
      <p className="logo-tagline">Guided by Light. Powered by Intelligence.</p>
    </div>
  )
}
