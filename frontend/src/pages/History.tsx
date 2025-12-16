import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
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
  compliance_scans: number
  total_zombies_found: number
  total_recommendations: number
  total_violations_found: number
  current_monthly_waste: number
  current_annual_savings_potential: number
  current_violations: number
}

function History() {
  const [scans, setScans] = useState<Scan[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'zombie' | 'rightsizing' | 'compliance'>('zombie')

  useEffect(() => {
    loadHistory()
    loadStats()
  }, [filter])

  const loadHistory = async () => {
    setLoading(true)
    try {
      const response = await fetch(`http://localhost:8000/api/history/scans?scan_type=${filter}`)
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

  const getScanIcon = (type: string) => {
    switch(type) {
      case 'zombie': return '💀'
      case 'rightsizing': return '📏'
      case 'compliance': return '🔒'
      default: return '•'
    }
  }

  const getTrendData = () => {
    return scans.slice().reverse().map(scan => ({
      date: new Date(scan.timestamp).toLocaleDateString(),
      time: new Date(scan.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
      value: filter === 'zombie' ? scan.total_cost :
             filter === 'rightsizing' ? scan.total_savings / 12 :
             scan.total_resources
    }))
  }

  const getChartLabel = () => {
    switch(filter) {
      case 'zombie': return 'Monthly Cost ($)'
      case 'rightsizing': return 'Monthly Savings ($)'
      case 'compliance': return 'Violations'
      default: return 'Value'
    }
  }

  const getChartColor = () => {
    switch(filter) {
      case 'zombie': return '#ff6b6b'
      case 'rightsizing': return '#42d392'
      case 'compliance': return '#ffa500'
      default: return '#646cff'
    }
  }

  const trendData = getTrendData()

  const renderStatsCards = () => {
    if (!stats) return null

    if (filter === 'zombie') {
      const avgCost = scans.length > 0 
        ? scans.reduce((sum, s) => sum + s.total_cost, 0) / scans.length 
        : 0

      return (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Scans</h3>
            <p className="stat-value">{stats.zombie_scans}</p>
          </div>
          <div className="stat-card">
            <h3>Zombies Found</h3>
            <p className="stat-value">{stats.total_zombies_found}</p>
            <p className="stat-subtitle">across all scans</p>
          </div>
          <div className="stat-card">
            <h3>Current Cost</h3>
            <p className="stat-value">${stats.current_monthly_waste.toFixed(2)}</p>
            <p className="stat-subtitle">per month</p>
          </div>
          <div className="stat-card">
            <h3>Average Cost</h3>
            <p className="stat-value">${avgCost.toFixed(2)}</p>
            <p className="stat-subtitle">per scan</p>
          </div>
        </div>
      )
    }

    if (filter === 'rightsizing') {
      return (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Analyses</h3>
            <p className="stat-value">{stats.rightsizing_scans}</p>
          </div>
          <div className="stat-card">
            <h3>Recommendations</h3>
            <p className="stat-value">{stats.total_recommendations}</p>
            <p className="stat-subtitle">across all scans</p>
          </div>
          <div className="stat-card">
            <h3>Annual Savings</h3>
            <p className="stat-value">${stats.current_annual_savings_potential.toFixed(2)}</p>
            <p className="stat-subtitle">latest analysis</p>
          </div>
          <div className="stat-card">
            <h3>Monthly Savings</h3>
            <p className="stat-value">${(stats.current_annual_savings_potential / 12).toFixed(2)}</p>
            <p className="stat-subtitle">latest analysis</p>
          </div>
        </div>
      )
    }

    if (filter === 'compliance') {
      return (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Scans</h3>
            <p className="stat-value">{stats.compliance_scans}</p>
          </div>
          <div className="stat-card">
            <h3>Resources with Violations</h3>
            <p className="stat-value">{stats.total_violations_found}</p>
            <p className="stat-subtitle">unique resources flagged</p>
          </div>
          <div className="stat-card">
            <h3>Current Violations</h3>
            <p className="stat-value">{stats.current_violations}</p>
            <p className="stat-subtitle">latest scan</p>
          </div>
          <div className="stat-card">
            <h3>Trend</h3>
            <p className="stat-value" style={{color: scans.length >= 2 && scans[0].total_resources < scans[1].total_resources ? '#42d392' : '#ff6b6b'}}>
              {scans.length >= 2 
                ? scans[0].total_resources < scans[1].total_resources ? '↓ Improving' : '↑ Worsening'
                : '—'}
            </p>
            <p className="stat-subtitle">vs previous scan</p>
          </div>
        </div>
      )
    }
  }

  return (
    <div className="history-page">
      <div className="history-header">
        <h1>📊 Scan History</h1>
        <div className="filter-buttons">
          <button 
            className={filter === 'zombie' ? 'active' : ''} 
            onClick={() => setFilter('zombie')}
          >
            💀 Zombie Hunter
          </button>
          <button 
            className={filter === 'rightsizing' ? 'active' : ''} 
            onClick={() => setFilter('rightsizing')}
          >
            📏 Right-Sizing
          </button>
          <button 
            className={filter === 'compliance' ? 'active' : ''} 
            onClick={() => setFilter('compliance')}
          >
            🔒 Compliance
          </button>
        </div>
      </div>

      {renderStatsCards()}

      {scans.length > 0 && (
        <div className="charts-grid">
          <div className="chart-card full-width">
            <h3>{filter === 'zombie' ? 'Zombie Cost Trend' : 
                 filter === 'rightsizing' ? 'Savings Potential Trend' :
                 'Violations Trend'}</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="date" stroke="#888" />
                <YAxis stroke="#888" />
                <Tooltip 
                  contentStyle={{ background: '#1a1a1a', border: '1px solid #333' }}
                  labelFormatter={(label) => {
                    const item = trendData.find(d => d.date === label)
                    return item ? `${label} ${item.time}` : label
                  }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke={getChartColor()} 
                  name={getChartLabel()}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

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
                    {getScanIcon(scan.scan_type)} {scan.scan_type}
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
                  {scan.scan_type === 'compliance' && (
                    <p><strong>Violations:</strong> {scan.total_resources}</p>
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
