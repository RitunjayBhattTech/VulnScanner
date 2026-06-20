import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function AdminPage() {
  const { user, isAdmin } = useAuth()
  const navigate = useNavigate()
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAdmin) { navigate('/'); return }
    fetchUsers()
  }, [isAdmin])

  async function fetchUsers() {
    try {
      const res = await fetch(`${API}/api/auth/admin/users`, {
        headers: { Authorization: `Bearer ${user?.access_token}` }
      })
      const data = await res.json()
      setUsers(Array.isArray(data) ? data : [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function toggleUser(userId: string, currentStatus: boolean) {
    await fetch(`${API}/api/auth/admin/users/${userId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${user?.access_token}`
      },
      body: JSON.stringify({ is_active: !currentStatus })
    })
    fetchUsers()
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ color: 'white', fontSize: '24px', fontWeight: 700 }}>Admin Panel</h1>
        <p style={{ color: '#64748b', fontSize: '14px', marginTop: '4px' }}>Manage users and system access</p>
      </div>

      <div style={{ background: '#0f1629', border: '1px solid #1e2a45', borderRadius: '12px', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #1e2a45', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ color: 'white', fontWeight: 600 }}>All Users ({users.length})</span>
        </div>

        {loading ? (
          <div style={{ color: '#64748b', textAlign: 'center', padding: '48px' }}>Loading...</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ background: '#1a2238' }}>
                {['Username', 'Email', 'Role', 'Status', 'Last Login', 'Actions'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '12px 16px', color: '#64748b', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u, i) => (
                <tr key={u.id} style={{ borderTop: '1px solid #1e2a45' }}>
                  <td style={{ padding: '14px 16px', color: 'white', fontWeight: 500 }}>
                    {u.username}
                    {u.id === user?.user_id && <span style={{ marginLeft: '8px', fontSize: '11px', color: '#3b82f6' }}>(you)</span>}
                  </td>
                  <td style={{ padding: '14px 16px', color: '#94a3b8', fontSize: '13px' }}>{u.email}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{
                      padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600,
                      background: u.role === 'admin' ? '#1e3a5f' : '#1a2238',
                      color: u.role === 'admin' ? '#60a5fa' : '#94a3b8',
                      border: u.role === 'admin' ? '1px solid #1e40af' : '1px solid #1e2a45',
                    }}>
                      {u.role.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{
                      padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600,
                      background: u.is_active ? '#14532d33' : '#7f1d1d33',
                      color: u.is_active ? '#4ade80' : '#f87171',
                      border: u.is_active ? '1px solid #166534' : '1px solid #991b1b',
                    }}>
                      {u.is_active ? 'ACTIVE' : 'DISABLED'}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', color: '#64748b', fontSize: '13px' }}>
                    {u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Never'}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    {u.id !== user?.user_id && (
                      <button
                        onClick={() => toggleUser(u.id, u.is_active)}
                        style={{
                          padding: '4px 12px',
                          borderRadius: '6px',
                          border: 'none',
                          background: u.is_active ? '#7f1d1d33' : '#14532d33',
                          color: u.is_active ? '#f87171' : '#4ade80',
                          fontSize: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        {u.is_active ? 'Disable' : 'Enable'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}