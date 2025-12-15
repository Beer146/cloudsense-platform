import { useState, useEffect } from 'react'
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './History.css'

interface Scan {
  id: number
  scan_type: string
  status: string
  regions: string[]
  total_resources: number
  total_cost: number
  total_savings: number
  timestamp: string
  duration_seconds: number
}

interface Stats {
  total_scans: number
  zombie_scans: number
  rightsizing_scans: number
  total_zombies_found: number
  total_recommendations: number
  current_monthly_waste: number
  current_annual_savings_potential: number
}

const COLORS = ['#646cff', '#42d392', '#ff6b6b', '#ffd93d']

function History() {
  const [scans, setScans] = useState<Scan[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'zombie' | 'rightsizing'>('all')

  useEffect(() => {
    loadHistory()
    loadStats()
  }, [filter])

  const loadHistory = async () => {
    setLoading(true)
    try {
      const filterParam = filter !== 'all' ? `?scan_type=${filter}` : ''
      const response = await fetch(`http://localhost:8000/api/history/scans${filterParam}`)
      const data = await response.json()
      setScans(data.scans || [])
    } catch (error) {
      console.error('Failed to load history:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/history/stats')
      const data = await response.json()
      setStats(data.stats)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const deleteScan = async (scanId: number) => {
    if (!confirm('Are you sure you want to delete this scan?')) return
    
    try {
      await fetch(`http://localhost:8000/api/history/scans/${scanId}`, {
        method: 'DELETE'
      })
      loadHistory()
      loadStats()
    } catch (error) {
      console.error('Failed to delete scan:', error)
    }
  }

  // Prepare chart data
  const trendData = scans.slice().reverse().map(scan => ({
    date: new Date(scan.timestamp).toLocaleDateString(),
    cost: scan.total_cost,
    savings: scan.total_savings
  }))

  const pieData = stats ? [
    { name: 'Zombie Scans', value: stats.zombie_scans },
    { name: 'Right-Sizing Scans', value: stats.rightsizing_scans }
  ] : []

  return (
    <div className="history-page">
      <div className="history-header">
        <h1>📊 Scan History</h1>
        <div className="filter-buttons">
          <button 
            className={filter === 'all' ? 'active' : ''} 
            onClick={() => setFilter('all')}
          >
            All Scans
          </button>
          <button 
            className={filter === 'zombie' ? 'active' : ''} 
            onClick={() => setFilter('zombie')}
          >
            Zombie Hunter
          </button>
          <button 
            className={filter === 'rightsizing' ? 'active' : ''} 
            onClick={() => setFilter('rightsizing')}
          >
            Right-Sizing
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Scans</h3>
            <p className="stat-value">{stats.total_scans}</p>
          </div>
          <div className="stat-card">
            <h3>Zombies Found</h3>
            <p className="stat-value">{stats.total_zombies_found}</p>
          </div>
          <div className="stat-card">
            <h3>Current Monthly Waste</h3>
            <p className="stat-value">${stats.current_monthly_waste.toFixed(2)}</p>
            <p className="stat-subtitle">from latest scan</p>
          </div>
          <div className="stat-card">
            <h3>Annual Savings Potential</h3>
            <p className="stat-value">${stats.current_annual_savings_potential.toFixed(2)}</p>
            <p className="stat-subtitle">from latest analysis</p>
          </div>
        </div>
      )}

      {/* Charts */}
      {scans.length > 0 && (
        <div className="charts-grid">
          <div className="chart-card">
            <h3>Cost Trend Over Time</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="date" stroke="#888" />
                <YAxis stroke="#888" />
                <Tooltip 
                  contentStyle={{ background: '#1a1a1a', border: '1px solid #333' }}
                />
                <Legend />
                <Line type="monotone" dataKey="cost" stroke="#ff6b6b" name="Monthly Cost" />
                <Line type="monotone" dataKey="savings" stroke="#42d392" name="Potential Savings" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {pieData.length > 0 && (
            <div className="chart-card">
              <h3>Scan Distribution</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => entry.name}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ background: '#1a1a1a', border: '1px solid #333' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Scan List */}
      <div className="scans-list">
        <h2>Recent Scans</h2>
        {loading ? (
          <p>Loading...</p>
        ) : scans.length === 0 ? (
          <p className="empty-state">No scans found. Run a scan to get started!</p>
        ) : (
          <div className="scan-cards">
            {scans.map(scan => (
              <div key={scan.id} className="scan-card">
                <div className="scan-header">
                  <span className={`scan-type ${scan.scan_type}`}>
                    {scan.scan_type === 'zombie' ? '💀' : '📏'} {scan.scan_type}
                  </span>
                  <span className="scan-date">
                    {new Date(scan.timestamp).toLocaleString()}
                  </span>
                </div>
                
                <div className="scan-details">
                  <p><strong>Regions:</strong> {scan.regions.join(', ')}</p>
                  <p><strong>Resources:</strong> {scan.total_resources}</p>
                  {scan.scan_type === 'zombie' && (
                    <p><strong>Monthly Cost:</strong> ${scan.total_cost.toFixed(2)}</p>
                  )}
                  {scan.scan_type === 'rightsizing' && (
                    <p><strong>Potential Savings:</strong> ${scan.total_savings.toFixed(2)}/year</p>
                  )}
                  <p><strong>Duration:</strong> {scan.duration_seconds?.toFixed(1)}s</p>
                </div>

                <div className="scan-actions">
                  <button 
                    className="delete-btn"
                    onClick={() => deleteScan(scan.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default History
