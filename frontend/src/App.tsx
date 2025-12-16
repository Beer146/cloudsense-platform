import { useState } from 'react'
import History from './pages/History'
import Insights from './pages/Insights'
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

interface Violation {
  id?: number
  resource_type: string
  resource_id: string
  resource_name?: string
  violation: string
  severity: string
  description: string
  remediation: string
  resolved?: boolean
  resolved_at?: string
  resolved_note?: string
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
  violations?: Violation[]
}

function App() {
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'history' | 'insights'>('dashboard')
  const [zombieResults, setZombieResults] = useState<ZombieResults | null>(null)
  const [rightSizingResults, setRightSizingResults] = useState<RightSizingResults | null>(null)
  const [complianceResults, setComplianceResults] = useState<ComplianceResults | null>(null)
  const [loading, setLoading] = useState<{ [key: string]: boolean }>({})
  const [showViolations, setShowViolations] = useState(false)
  const [resolvingViolation, setResolvingViolation] = useState<number | null>(null)

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
    setShowViolations(false)
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

  const markViolationResolved = async (violationId: number, index: number) => {
    if (!complianceResults || !complianceResults.violations) return
    
    const note = prompt('Add a note about how you fixed this (optional):')
    
    setResolvingViolation(violationId)
    try {
      const response = await fetch(`http://localhost:8000/api/resolutions/compliance/${violationId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note: note || undefined })
      })
      
      if (response.ok) {
        const updatedViolations = [...complianceResults.violations]
        updatedViolations[index] = {
          ...updatedViolations[index],
          resolved: true,
          resolved_at: new Date().toISOString(),
          resolved_note: note || undefined
        }
        
        setComplianceResults({
          ...complianceResults,
          violations: updatedViolations
        })
        
        alert('✅ Violation marked as resolved!')
      } else {
        alert('Failed to mark violation as resolved')
      }
    } catch (error) {
      console.error('Failed to resolve violation:', error)
      alert('Error marking violation as resolved')
    } finally {
      setResolvingViolation(null)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch(severity) {
      case 'critical': return '#D13212'
      case 'high': return '#FF9900'
      case 'medium': return '#FFD700'
      case 'low': return '#146EB4'
      default: return '#888'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch(severity) {
      case 'critical': return '🚨'
      case 'high': return '⚠️'
      case 'medium': return '⚡'
      case 'low': return 'ℹ️'
      default: return '•'
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
            <button onClick={() => setCurrentPage('insights')}>Insights</button>
          </div>
        </nav>
        <History />
      </div>
    )
  }

  if (currentPage === 'insights') {
    return (
      <div className="App">
        <nav className="main-nav">
          <h1>CloudSense Platform</h1>
          <div className="nav-buttons">
            <button onClick={() => setCurrentPage('dashboard')}>Dashboard</button>
            <button onClick={() => setCurrentPage('history')}>History</button>
            <button className="active" onClick={() => setCurrentPage('insights')}>Insights</button>
          </div>
        </nav>
        <Insights />
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
          <button onClick={() => setCurrentPage('insights')}>Insights</button>
        </div>
      </nav>

      <div className="dashboard-content">
        <div className="dashboard-header">
          <h1>AWS Cost Optimization Dashboard</h1>
          <p className="subtitle">Unified AWS Cost Optimization & Security Suite</p>
        </div>

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

                {(complianceResults.total_violations ?? 0) > 0 && complianceResults.violations && (
                  <button 
                    onClick={() => setShowViolations(!showViolations)}
                    style={{ marginTop: '1rem', background: '#D13212' }}
                  >
                    {showViolations ? 'Hide Details' : 'Show Violation Details'}
                  </button>
                )}
                
                {complianceResults.scan_id && (
                  <p className="info-message">✅ Saved to history (ID: {complianceResults.scan_id})</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Violation Details Modal */}
        {showViolations && complianceResults && complianceResults.violations && (
          <div className="violations-modal">
            <div className="violations-content">
              <div className="violations-header">
                <h2>🔒 Compliance Violations</h2>
                <button className="close-btn" onClick={() => setShowViolations(false)}>✕</button>
              </div>
              
              <div className="violations-list">
                {complianceResults.violations.map((violation, index) => (
                  <div 
                    key={index} 
                    className={`violation-card ${violation.resolved ? 'resolved' : ''}`}
                    style={{ borderLeft: `4px solid ${violation.resolved ? '#1D8102' : getSeverityColor(violation.severity)}` }}
                  >
                    <div className="violation-header">
                      <span className="severity-badge" style={{ background: violation.resolved ? '#1D8102' : getSeverityColor(violation.severity) }}>
                        {violation.resolved ? '✅ RESOLVED' : `${getSeverityIcon(violation.severity)} ${violation.severity.toUpperCase()}`}
                      </span>
                      <span className="resource-type">{violation.resource_type}</span>
                    </div>
                    
                    <div className="violation-body">
                      <p className="resource-id"><strong>Resource:</strong> {violation.resource_id}</p>
                      {violation.resource_name && (
                        <p className="resource-name"><strong>Name:</strong> {violation.resource_name}</p>
                      )}
                      <p className="description">{violation.description}</p>
                      
                      {!violation.resolved && (
                        <div className="remediation">
                          <strong>🔧 Remediation:</strong>
                          <p>{violation.remediation}</p>
                        </div>
                      )}

                      {violation.resolved && (
                        <div className="resolved-info">
                          <p><strong>✅ Marked as fixed:</strong> {new Date(violation.resolved_at!).toLocaleString()}</p>
                          {violation.resolved_note && (
                            <p><strong>Note:</strong> {violation.resolved_note}</p>
                          )}
                        </div>
                      )}

                      {!violation.resolved && violation.id && (
                        <button
                          className="resolve-btn"
                          onClick={() => markViolationResolved(violation.id!, index)}
                          disabled={resolvingViolation === violation.id}
                        >
                          {resolvingViolation === violation.id ? 'Marking as Fixed...' : '✓ Mark as Fixed'}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
