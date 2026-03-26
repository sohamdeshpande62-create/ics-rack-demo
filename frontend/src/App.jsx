import { BrowserRouter, Routes, Route } from 'react-router-dom'
import RackManager from './pages/RackManager.jsx'
import RackDisplay from './pages/RackDisplay.jsx'
import RackEditor from './pages/RackEditor.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"       element={<RackManager />} />
        <Route path="/display" element={<RackDisplay />} />
        <Route path="/edit"    element={<RackEditor />} />
      </Routes>
    </BrowserRouter>
  )
}
