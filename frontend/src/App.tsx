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

interface ComplianceResults {
  status: string
  scan_id?: number
  regions_scanned?: string[]
  total_violations?: number
  by_severity?: {
    critical: number
    high: number
    medium: number
    low: number
  }
  by_type?: any
  violations?: any[]
}

function App() {
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'history'>('dashboard')
  const [apiStatus, setApiStatus] = useState<string>('Checking...')
  const [zombieResults, setZombieResults] = useState<ZombieResults | null>(null)
  const [rightSizingResults, setRightSizingResults] = useState<RightSizingResults | null>(null)
  const [complianceResults, setComplianceResults] = useState<ComplianceResults | null>(null)
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

  const runComplianceScan = async () => {
    setLoading({ ...loading, compliance: true })
    try {
      const response = await fetch('http://localhost:8000/api/compliance/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      const data = await response.json()
      setComplianceResults(data)
    } catch (error) {
      console.error('Compliance scan failed:', error)
      setComplianceResults({ status: 'error' })
    } finally {
      setLoading({ ...loading, compliance: false })
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
        <p className="subtitle">Unified AWS Cost Optimization & Security Suite</p>
        
        <button onClick={checkAPI} className="test-btn">Test API Connection</button>
        <p className="api-status">{apiStatus}</p>

        <div className="service-grid">
          {/* Zombie Resource Hunter */}
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
                  <p className="success-message">🎉 No zombie resources found!</p>
                )}
                
                {zombieResults.scan_id && (
                  <p className="info-message">✅ Saved to history (ID: {zombieResults.scan_id})</p>
                )}
              </div>
            )}
          </div>

          {/* Right-Sizing Engine */}
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
                
                <p><strong>EC2 Analyzed:</strong> {rightSizingResults.recommendations?.ec2?.total_analyzed || 0}</p>
                <p><strong>Potential Savings:</strong> ${rightSizingResults.total_monthly_savings?.toFixed(2)}/month</p>
                <p><strong>Regions:</strong> {rightSizingResults.regions_analyzed?.join(', ')}</p>
                
                <div className="breakdown">
                  <p>Downsize: {rightSizingResults.recommendations?.ec2?.downsize_opportunities || 0}</p>
                  <p>Family Switch: {rightSizingResults.recommendations?.ec2?.family_switches || 0}</p>
                </div>

                {(rightSizingResults.total_monthly_savings || 0) === 0 && 
                 (rightSizingResults.recommendations?.ec2?.total_analyzed || 0) === 0 && (
                  <p className="info-message">💡 No running instances found.</p>
                )}

                {(rightSizingResults.total_monthly_savings || 0) === 0 && 
                 (rightSizingResults.recommendations?.ec2?.total_analyzed || 0) > 0 && (
                  <p className="success-message">🎉 Already optimized!</p>
                )}
                
                {rightSizingResults.scan_id && (
                  <p className="info-message">✅ Saved to history (ID: {rightSizingResults.scan_id})</p>
                )}
              </div>
            )}
          </div>

          {/* Compliance Validator */}
          <div className="service-card">
            <h2>🔒 Compliance Validator</h2>
            <p>Check AWS resources for security violations</p>
            <button onClick={runComplianceScan} disabled={loading.compliance}>
              {loading.compliance ? 'Scanning...' : 'Run Compliance Scan'}
            </button>

            {complianceResults && complianceResults.status === 'success' && (
              <div className="results">
                <h3>Results:</h3>
                <p><strong>Total Violations:</strong> {complianceResults.total_violations}</p>
                <p><strong>Regions:</strong> {complianceResults.regions_scanned?.join(', ')}</p>
                
                <div className="breakdown">
                  <p className="critical">🚨 Critical: {complianceResults.by_severity?.critical || 0}</p>
                  <p className="high">⚠️ High: {complianceResults.by_severity?.high || 0}</p>
                  <p className="medium">⚡ Medium: {complianceResults.by_severity?.medium || 0}</p>
                  <p className="low">ℹ️ Low: {complianceResults.by_severity?.low || 0}</p>
                </div>

                <div className="breakdown" style={{marginTop: '1rem', paddingTop: '1rem'}}>
                  <p>S3: {complianceResults.by_type?.s3 || 0}</p>
                  <p>RDS: {complianceResults.by_type?.rds || 0}</p>
                  <p>Security Groups: {complianceResults.by_type?.security_group || 0}</p>
                  <p>EC2: {complianceResults.by_type?.ec2 || 0}</p>
                </div>

                {complianceResults.total_violations === 0 && (
                  <p className="success-message">🎉 Fully compliant!</p>
                )}
                
                {complianceResults.scan_id && (
                  <p className="info-message">✅ Saved to history (ID: {complianceResults.scan_id})</p>
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
