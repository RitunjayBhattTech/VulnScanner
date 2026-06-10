import React, { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import { checkBackendHealth } from './api'
import ScanDashboard from './components/ScanDashboard'
import NewScan from './components/NewScan'
import ScanDetail from './components/ScanDetail'

export default function App() {
  const [backendOnline, setBackendOnline] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const check = () => checkBackendHealth().then(setBackendOnline).catch(() => setBackendOnline(false))
    check()
    const interval = setInterval(check, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app">
      <nav className="nav">
        <NavLink to="/" className="nav-title">
          🔍 VulnScanner AI
        </NavLink>
        <div className="nav-links">
          <NavLink to="/" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
            Dashboard
          </NavLink>
          <NavLink to="/new-scan" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
            New Scan
          </NavLink>
        </div>
        <div className="nav-status">
          <span className={`status-dot ${backendOnline ? 'online' : 'offline'}`} />
          {backendOnline ? 'Backend Online' : 'Backend Offline'}
        </div>
      </nav>

      <main className="main">
        <Routes>
          <Route path="/" element={<ScanDashboard />} />
          <Route path="/new-scan" element={<NewScan />} />
          <Route path="/scans/:scanId" element={<ScanDetail />} />
        </Routes>
      </main>
    </div>
  )
}