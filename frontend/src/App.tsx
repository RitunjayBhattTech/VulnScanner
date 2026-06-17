import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ScanPage from './pages/ScanPage'
import ScansListPage from './pages/ScansListPage'
import FindingsPage from './pages/FindingsPage'
import ErrorBoundary from './components/ErrorBoundary'

const S = {
  sidebar: {
    position: 'fixed' as const, left: 0, top: 0, height: '100%', width: '224px',
    background: '#0f1629', borderRight: '1px solid #1e2a45',
    display: 'flex', flexDirection: 'column' as const, zIndex: 50,
  },
  logo: {
    padding: '24px', borderBottom: '1px solid #1e2a45',
    display: 'flex', alignItems: 'center', gap: '12px',
  },
  logoIcon: {
    width: '36px', height: '36px',
    background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
    borderRadius: '10px', display: 'flex', alignItems: 'center',
    justifyContent: 'center', color: 'white', fontWeight: 'bold' as const,
    fontSize: '16px', flexShrink: 0,
  },
  nav: { flex: 1, padding: '16px', display: 'flex', flexDirection: 'column' as const, gap: '4px' },
  main: { marginLeft: '224px', flex: 1, padding: '32px', minHeight: '100vh' },
  footer: { padding: '16px', borderTop: '1px solid #1e2a45', textAlign: 'center' as const },
}

function NavItem({ to, label, icon, end }: { to: string; label: string; icon: string; end?: boolean }) {
  return (
    <NavLink to={to} end={end} style={({ isActive }) => ({
      display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px',
      borderRadius: '8px', fontSize: '14px', fontWeight: 500, textDecoration: 'none',
      transition: 'all 0.15s',
      background: isActive ? '#3b82f6' : 'transparent',
      color: isActive ? '#ffffff' : '#94a3b8',
    })}>
      <span style={{ fontSize: '18px' }}>{icon}</span>
      {label}
    </NavLink>
  )
}

function Sidebar() {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: '⬡' },
    { to: '/scans', label: 'All Scans', icon: '◎' },
    { to: '/findings', label: 'Findings', icon: '◈' },
  ]

  return (
    <aside style={S.sidebar}>
      <div style={S.logo}>
        <div style={S.logoIcon}>V</div>
        <div>
          <div style={{ color: 'white', fontWeight: 700, fontSize: '15px' }}>VulnAI</div>
          <div style={{ color: '#3b82f6', fontSize: '11px', fontWeight: 500 }}>SCANNER</div>
        </div>
      </div>
      <nav style={S.nav}>
        {navItems.map(item => (
          <NavItem key={item.to} to={item.to} label={item.label} icon={item.icon} end={item.to === '/'} />
        ))}
      </nav>
      <div style={S.footer}>
        <span style={{ color: '#475569', fontSize: '11px' }}>Authorised testing only</span>
      </div>
    </aside>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div style={{ display: 'flex', minHeight: '100vh', background: '#0a0e1a' }}>
          <Sidebar />
          <main style={S.main}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/scans" element={<ScansListPage />} />
              <Route path="/scans/:scanId" element={<ScanPage />} />
              <Route path="/findings" element={<FindingsPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  )
}