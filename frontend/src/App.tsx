import { useState } from 'react'
import History from './pages/History'
import './App.css'

interface ZombieResults {
  status: string
  scan_id?: number
  regions_scanned?: string[]
  total_zombies?: number
  total_monthly_cost?: number
  zombies_found?: any
}

interface RightSizingResults {
  status: string
  scan_id?: number
  regions_analyzed?: string[]
  total_monthly_savings?: number
  recommendations?: any
  message?: string
}

function App() {
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'history'>('dashboard')
  const [apiStatus, setApiStatus] = useState<string>('Checking...')
  const [zombieResults, setZombieResults] = useState<ZombieResults | null>(null)
  const [rightSizingResults, setRightSizingResults] = useState<RightSizingResults | null>(null)
  const [loading, setLoading] = useState<{ [key: string]: boolean }>({})

  const checkAPI = async () => {
    try {
      const response = await fetch('http://localhost:8000/')
      const data = await response.json()
      setApiStatus(`✅ Connected: ${data.message}`)
    } catch (error) {
      setApiStatus('❌ API not reachable')
    }
  }

  const runZombieScan = async () => {
    setLoading({ ...loading, zombie: true })
    try {
      const response = await fetch('http://localhost:8000/api/zombie/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      const data = await response.json()
      setZombieResults(data)
    } catch (error) {
      console.error('Zombie scan failed:', error)
      setZombieResults({ status: 'error' })
    } finally {
      setLoading({ ...loading, zombie: false })
    }
  }

  const runRightSizing = async () => {
    setLoading({ ...loading, rightsizing: true })
    try {
      const response = await fetch('http://localhost:8000/api/rightsizing/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      const data = await response.json()
      setRightSizingResults(data)
    } catch (error) {
      console.error('Right-sizing analysis failed:', error)
      setRightSizingResults({ status: 'error' })
    } finally {
      setLoading({ ...loading, rightsizing: false })
    }
  }

  if (currentPage === 'history') {
    return (
      <div className="App">
        <nav className="main-nav">
          <h1>CloudSense Platform</h1>
          <div className="nav-buttons">
            <button onClick={() => setCurrentPage('dashboard')}>Dashboard</button>
            <button className="active" onClick={() => setCurrentPage('history')}>History</button>
          </div>
        </nav>
        <History />
      </div>
    )
  }

  return (
    <div className="App">
      <nav className="main-nav">
        <h1>CloudSense Platform</h1>
        <div className="nav-buttons">
          <button className="active" onClick={() => setCurrentPage('dashboard')}>Dashboard</button>
          <button onClick={() => setCurrentPage('history')}>History</button>
        </div>
      </nav>

      <div className="dashboard-content">
        <p className="subtitle">Unified AWS Cost Optimization Suite</p>
        
        <button onClick={checkAPI} className="test-btn">Test API Connection</button>
        <p className="api-status">{apiStatus}</p>

        <div className="service-grid">
          <div className="service-card">
            <h2>💀 Zombie Resource Hunter</h2>
            <p>Find and eliminate unused AWS resources</p>
            <button onClick={runZombieScan} disabled={loading.zombie}>
              {loading.zombie ? 'Scanning...' : 'Run Scan'}
            </button>

            {zombieResults && zombieResults.status === 'success' && (
              <div className="results">
                <h3>Results:</h3>
                <p><strong>Zombies Found:</strong> {zombieResults.total_zombies}</p>
                <p><strong>Monthly Cost:</strong> ${zombieResults.total_monthly_cost?.toFixed(2)}</p>
                <p><strong>Regions:</strong> {zombieResults.regions_scanned?.join(', ')}</p>
                
                <div className="breakdown">
                  <p>EC2: {zombieResults.zombies_found?.ec2?.count || 0} instances</p>
                  <p>EBS: {zombieResults.zombies_found?.ebs?.count || 0} volumes</p>
                  <p>RDS: {zombieResults.zombies_found?.rds?.count || 0} databases</p>
                  <p>ELB: {zombieResults.zombies_found?.elb?.count || 0} load balancers</p>
                </div>

                {zombieResults.total_zombies === 0 && (
                  <p className="success-message">🎉 No zombie resources found - your AWS is clean!</p>
                )}
                
                {zombieResults.scan_id && (
                  <p className="info-message">✅ Scan saved to history (ID: {zombieResults.scan_id})</p>
                )}
              </div>
            )}
          </div>

          <div className="service-card">
            <h2>📏 Right-Sizing Engine</h2>
            <p>Optimize instance types based on usage</p>
            <button onClick={runRightSizing} disabled={loading.rightsizing}>
              {loading.rightsizing ? 'Analyzing...' : 'Analyze Resources'}
            </button>

            {rightSizingResults && rightSizingResults.status === 'success' && (
              <div className="results">
                <h3>Results:</h3>
                
                {rightSizingResults.message && (
                  <p className="info-message">ℹ️ {rightSizingResults.message}</p>
                )}
                
                <p><strong>EC2 Analyzed:</strong> {rightSizingResults.recommendations?.ec2?.total_analyzed || 0} instances</p>
                <p><strong>Potential Savings:</strong> ${rightSizingResults.total_monthly_savings?.toFixed(2)}/month</p>
                <p><strong>Regions:</strong> {rightSizingResults.regions_analyzed?.join(', ')}</p>
                
                <div className="breakdown">
                  <p>Downsize: {rightSizingResults.recommendations?.ec2?.downsize_opportunities || 0} opportunities</p>
                  <p>Family Switch: {rightSizingResults.recommendations?.ec2?.family_switches || 0} opportunities</p>
                </div>

                {(rightSizingResults.total_monthly_savings || 0) === 0 && 
                 (rightSizingResults.recommendations?.ec2?.total_analyzed || 0) === 0 && (
                  <p className="info-message">💡 No running instances found. Right-sizing only analyzes running resources.</p>
                )}

                {(rightSizingResults.total_monthly_savings || 0) === 0 && 
                 (rightSizingResults.recommendations?.ec2?.total_analyzed || 0) > 0 && (
                  <p className="success-message">🎉 Your instances are already well-optimized!</p>
                )}
                
                {rightSizingResults.scan_id && (
                  <p className="info-message">✅ Analysis saved to history (ID: {rightSizingResults.scan_id})</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
