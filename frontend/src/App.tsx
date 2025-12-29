import { useState } from 'react'
import { useAuth } from '@clerk/clerk-react'
import Navbar from './components/Navbar'
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
  at_risk_resources?: any[]
  at_risk_count?: number
}

interface RightSizingResults {
  status: string
  scan_id?: number
  regions_analyzed?: string[]
  total_monthly_savings?: number
  recommendations?: any
  message?: string
  total_analyzed?: number
  lstm_enhanced_count?: number
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
  rule_based_violations?: number
  ml_anomalies?: number
  baseline_trained?: boolean
  by_severity?: {
    critical: number
    high: number
    medium: number
    low: number
  }
  by_type?: any
  violations?: Violation[]
}

interface PostMortemResults {
  status: string
  scan_id?: number
  message?: string
  regions_analyzed?: string[]
  lookback_hours?: number
  summary?: {
    total_errors: number
    total_warnings: number
    unique_patterns?: number
  }
  recommendations?: string[]
  error_patterns?: any[]
  llm_analysis?: {
    executive_summary?: string
    root_causes?: Array<{
      title: string
      description: string
      evidence: string
      impact: string
      affected_services: string[]
    }>
    recommendations?: Array<{
      priority: string
      title: string
      description: string
      aws_service: string
      documentation_link?: string
    }>
    severity_assessment?: string
    affected_services?: string[]
    preventive_measures?: string[]
    redaction_stats?: Record<string, number>
  }
}

function App() {
  const { getToken } = useAuth()
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'history' | 'insights'>('dashboard')
  const [zombieResults, setZombieResults] = useState<ZombieResults | null>(null)
  const [rightSizingResults, setRightSizingResults] = useState<RightSizingResults | null>(null)
  const [complianceResults, setComplianceResults] = useState<ComplianceResults | null>(null)
  const [postMortemResults, setPostMortemResults] = useState<PostMortemResults | null>(null)
  const [loading, setLoading] = useState<{ [key: string]: boolean }>({})
  const [showViolations, setShowViolations] = useState(false)
  const [resolvingViolation, setResolvingViolation] = useState<number | null>(null)

  const runZombieScan = async () => {
    setLoading({ ...loading, zombie: true })
    try {
      const token = await getToken()
      const response = await fetch('http://localhost:8000/api/zombie/scan', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
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
      const token = await getToken()
      const response = await fetch('http://localhost:8000/api/rightsizing/analyze', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
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
      const token = await getToken()
      const response = await fetch('http://localhost:8000/api/compliance/scan', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
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

  const runPostMortemAnalysis = async () => {
    setLoading({ ...loading, postmortem: true })
    try {
      const token = await getToken()
      const response = await fetch('http://localhost:8000/api/postmortem/analyze', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ lookback_hours: 24 })
      })
      const data = await response.json()
      setPostMortemResults(data)
    } catch (error) {
      console.error('Post-mortem analysis failed:', error)
      setPostMortemResults({ status: 'error' })
    } finally {
      setLoading({ ...loading, postmortem: false })
    }
  }

  const markViolationResolved = async (violationId: number, index: number) => {
    if (!complianceResults || !complianceResults.violations) return
    
    const note = prompt('Add a note about how you fixed this (optional):')
    
    setResolvingViolation(violationId)
    try {
      const token = await getToken()
      const response = await fetch(`http://localhost:8000/api/resolutions/compliance/${violationId}/resolve`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
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
        <Navbar currentPage={currentPage} onNavigate={setCurrentPage} />
        <History />
      </div>
    )
  }

  if (currentPage === 'insights') {
    return (
      <div className="App">
        <Navbar currentPage={currentPage} onNavigate={setCurrentPage} />
        <Insights />
      </div>
    )
  }

  return (
    <div className="App">
      <Navbar currentPage={currentPage} onNavigate={setCurrentPage} />

      <div className="dashboard-content">
        <div className="dashboard-header">
          <h1>AWS Cost Optimization Dashboard</h1>
          <p className="subtitle">Unified AWS Cost Optimization & Security Suite</p>
        </div>

        <div className="dashboard-grid-container">
          <div className="service-grid">
            {/* Zombie Resource Hunter with ML */}
            <div className="service-card">
              <h2>💀 Zombie Resource Hunter</h2>
              <p>Find and eliminate unused AWS resources with ML predictions</p>
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

                  {zombieResults.at_risk_count !== undefined && zombieResults.at_risk_count > 0 && (
                    <div className="breakdown" style={{marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #333'}}>
                      <p style={{color: '#ffa500', fontWeight: 'bold'}}>
                        🤖 ML Prediction: {zombieResults.at_risk_count} running resource{zombieResults.at_risk_count > 1 ? 's' : ''} at HIGH RISK of becoming zombie
                      </p>
                    </div>
                  )}

                  {zombieResults.total_zombies === 0 && (!zombieResults.at_risk_count || zombieResults.at_risk_count === 0) && (
                    <p className="success-message">🎉 No zombie resources found and no resources at risk!</p>
                  )}
                  
                  {zombieResults.scan_id && (
                    <p className="info-message">✅ Saved to history (ID: {zombieResults.scan_id})</p>
                  )}
                </div>
              )}
            </div>

            {/* Right-Sizing Engine with LSTM */}
            <div className="service-card">
              <h2>📏 Right-Sizing Engine</h2>
              <p>Optimize instance types with LSTM workload forecasting</p>
              <button onClick={runRightSizing} disabled={loading.rightsizing}>
                {loading.rightsizing ? 'Analyzing...' : 'Analyze Resources'}
              </button>

              {rightSizingResults && rightSizingResults.status === 'success' && (
                <div className="results">
                  <h3>Results:</h3>
                  
                  {rightSizingResults.message && (
                    <p className="info-message">ℹ️ {rightSizingResults.message}</p>
                  )}
                  
                  <p><strong>EC2 Analyzed:</strong> {rightSizingResults.total_analyzed || rightSizingResults.recommendations?.ec2?.total_analyzed || 0}</p>
                  <p><strong>Potential Savings:</strong> ${rightSizingResults.total_monthly_savings?.toFixed(2)}/month</p>
                  <p><strong>Regions:</strong> {rightSizingResults.regions_analyzed?.join(', ')}</p>
                  
                  {/* LSTM Enhancement Stats */}
                  {(rightSizingResults.lstm_enhanced_count !== undefined) && (
                    <div className="breakdown" style={{marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #333'}}>
                      <p style={{color: '#888'}}>📊 Traditional analysis: {(rightSizingResults.total_analyzed || 0) - (rightSizingResults.lstm_enhanced_count || 0)}</p>
                      <p style={{color: '#646cff'}}>🤖 LSTM-enhanced forecasts: {rightSizingResults.lstm_enhanced_count || 0}</p>
                      {rightSizingResults.lstm_enhanced_count > 0 && (
                        <p style={{color: '#42d392', fontSize: '0.9rem', marginTop: '0.5rem'}}>
                          ✅ Using neural networks for 7-day workload prediction
                        </p>
                      )}
                    </div>
                  )}
                  
                  <div className="breakdown">
                    <p>Downsize: {rightSizingResults.recommendations?.ec2?.downsize_opportunities || 0}</p>
                    <p>Family Switch: {rightSizingResults.recommendations?.ec2?.family_switches || 0}</p>
                  </div>

                  {(rightSizingResults.total_monthly_savings || 0) === 0 && 
                   (rightSizingResults.total_analyzed || rightSizingResults.recommendations?.ec2?.total_analyzed || 0) === 0 && (
                    <p className="info-message">💡 No running instances found.</p>
                  )}

                  {(rightSizingResults.total_monthly_savings || 0) === 0 && 
                   (rightSizingResults.total_analyzed || rightSizingResults.recommendations?.ec2?.total_analyzed || 0) > 0 && (
                    <p className="success-message">🎉 Already optimized!</p>
                  )}
                  
                  {rightSizingResults.scan_id && (
                    <p className="info-message">✅ Saved to history (ID: {rightSizingResults.scan_id})</p>
                  )}
                </div>
              )}
            </div>

            {/* Compliance Validator with ML Anomaly Detection */}
            <div className="service-card">
              <h2>🔒 Compliance Validator</h2>
              <p>Check AWS resources for security violations with ML anomaly detection</p>
              <button onClick={runComplianceScan} disabled={loading.compliance}>
                {loading.compliance ? 'Scanning...' : 'Run Compliance Scan'}
              </button>

              {complianceResults && complianceResults.status === 'success' && (
                <div className="results">
                  <h3>Results:</h3>
                  <p><strong>Total Violations:</strong> {complianceResults.total_violations}</p>
                  <p><strong>Regions:</strong> {complianceResults.regions_scanned?.join(', ')}</p>
                  
                  {/* ML Detection Stats */}
                  {(complianceResults.rule_based_violations !== undefined || complianceResults.ml_anomalies !== undefined) && (
                    <div className="breakdown" style={{marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #333'}}>
                      <p style={{color: '#888'}}>📋 Rule-based violations: {complianceResults.rule_based_violations || 0}</p>
                      <p style={{color: '#ffa500'}}>🤖 ML Anomalies detected: {complianceResults.ml_anomalies || 0}</p>
                      {complianceResults.baseline_trained && (
                        <p style={{color: '#42d392', fontSize: '0.9rem', marginTop: '0.5rem'}}>
                          ✅ Baseline model trained on infrastructure
                        </p>
                      )}
                      {!complianceResults.baseline_trained && complianceResults.ml_anomalies === 0 && (
                        <p style={{color: '#888', fontSize: '0.9rem', marginTop: '0.5rem'}}>
                          ℹ️ Need 2+ instances to train baseline
                        </p>
                      )}
                    </div>
                  )}
                  
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
                    <p>EC2: {complianceResults.by_type?.EC2 || 0}</p>
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

            {/* Post-Mortem Generator with LLM */}
            <div className="service-card">
              <h2>📋 Post-Mortem Generator</h2>
              <p>Analyze CloudWatch Logs with AI-powered root cause analysis</p>
              <button onClick={runPostMortemAnalysis} disabled={loading.postmortem}>
                {loading.postmortem ? 'Analyzing...' : 'Generate Report'}
              </button>

              {postMortemResults && postMortemResults.status === 'success' && (
                <div className="results">
                  <h3>Results:</h3>
                  
                  {postMortemResults.message && (
                    <p className="info-message">ℹ️ {postMortemResults.message}</p>
                  )}
                  
                  {postMortemResults.summary && (
                    <>
                      <p><strong>Errors Found:</strong> {postMortemResults.summary.total_errors}</p>
                      <p><strong>Warnings Found:</strong> {postMortemResults.summary.total_warnings}</p>
                      <p><strong>Lookback Period:</strong> {postMortemResults.lookback_hours} hours</p>
                      
                      <div className="breakdown">
                        <p>Unique Patterns: {postMortemResults.summary.unique_patterns || 0}</p>
                        <p>Regions: {postMortemResults.regions_analyzed?.join(', ')}</p>
                      </div>

                      {/* LLM Analysis Section */}
                      {postMortemResults.llm_analysis && (
                        <div className="breakdown" style={{marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '2px solid #646cff'}}>
                          <p style={{color: '#646cff', fontWeight: 'bold', marginBottom: '1rem'}}>
                            🤖 AI-Powered Analysis
                          </p>
                          
                          {/* Security: Show what was redacted */}
                          {postMortemResults.llm_analysis.redaction_stats && 
                           Object.keys(postMortemResults.llm_analysis.redaction_stats).length > 0 && (
                            <div style={{marginBottom: '1rem', padding: '0.75rem', background: 'rgba(76, 175, 80, 0.1)', borderRadius: '6px', borderLeft: '3px solid #4CAF50'}}>
                              <strong style={{color: '#4CAF50'}}>🔒 Security:</strong> 
                              <span style={{marginLeft: '0.5rem', fontSize: '0.9rem'}}>
                                {Object.entries(postMortemResults.llm_analysis.redaction_stats).reduce((sum, [_, count]) => sum + count, 0)} sensitive items redacted
                              </span>
                              <div style={{fontSize: '0.85rem', marginTop: '0.5rem', color: '#888'}}>
                                {Object.entries(postMortemResults.llm_analysis.redaction_stats).map(([type, count]) => (
                                  <span key={type} style={{marginRight: '1rem'}}>
                                    {type.replace(/_/g, ' ')}: {count}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Executive Summary */}
                          {postMortemResults.llm_analysis.executive_summary && (
                            <div style={{marginBottom: '1rem', padding: '1rem', background: 'rgba(100, 108, 255, 0.1)', borderRadius: '8px', borderLeft: '3px solid #646cff'}}>
                              <strong style={{color: '#646cff'}}>Executive Summary:</strong>
                              <p style={{marginTop: '0.5rem', fontSize: '0.95rem', lineHeight: '1.6'}}>
                                {postMortemResults.llm_analysis.executive_summary}
                              </p>
                            </div>
                          )}

                          {/* Severity Assessment */}
                          {postMortemResults.llm_analysis.severity_assessment && (
                            <p style={{marginBottom: '0.5rem'}}>
                              <strong>Severity:</strong> 
                              <span style={{
                                marginLeft: '0.5rem',
                                padding: '0.25rem 0.75rem',
                                borderRadius: '4px',
                                background: postMortemResults.llm_analysis.severity_assessment === 'CRITICAL' ? '#D13212' :
                                           postMortemResults.llm_analysis.severity_assessment === 'HIGH' ? '#FF9900' :
                                           postMortemResults.llm_analysis.severity_assessment === 'MEDIUM' ? '#FFD700' : '#146EB4',
                                color: 'white',
                                fontWeight: 'bold',
                                fontSize: '0.85rem'
                              }}>
                                {postMortemResults.llm_analysis.severity_assessment}
                              </span>
                            </p>
                          )}

                          {/* Root Causes */}
                          {postMortemResults.llm_analysis.root_causes && postMortemResults.llm_analysis.root_causes.length > 0 && (
                            <div style={{marginTop: '1rem'}}>
                              <strong style={{color: '#FF9900'}}>🔍 Root Causes Identified: {postMortemResults.llm_analysis.root_causes.length}</strong>
                              {postMortemResults.llm_analysis.root_causes.slice(0, 2).map((cause, i) => (
                                <div key={i} style={{marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(255, 153, 0, 0.1)', borderRadius: '6px', fontSize: '0.9rem'}}>
                                  <div style={{fontWeight: 'bold', color: '#FF9900'}}>{i + 1}. {cause.title}</div>
                                  <div style={{marginTop: '0.25rem', fontSize: '0.85rem'}}>{cause.description}</div>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Recommendations */}
                          {postMortemResults.llm_analysis.recommendations && postMortemResults.llm_analysis.recommendations.length > 0 && (
                            <div style={{marginTop: '1rem'}}>
                              <strong style={{color: '#42d392'}}>💡 AI Recommendations:</strong>
                              {postMortemResults.llm_analysis.recommendations.slice(0, 3).map((rec, i) => (
                                <div key={i} style={{marginTop: '0.5rem', fontSize: '0.9rem'}}>
                                  <span style={{
                                    padding: '0.2rem 0.5rem',
                                    borderRadius: '3px',
                                    background: rec.priority === 'CRITICAL' ? '#D13212' : rec.priority === 'HIGH' ? '#FF9900' : '#FFD700',
                                    color: 'white',
                                    fontSize: '0.75rem',
                                    fontWeight: 'bold',
                                    marginRight: '0.5rem'
                                  }}>
                                    {rec.priority}
                                  </span>
                                  <strong>{rec.title}</strong>
                                  {rec.documentation_link && (
                                    <a href={rec.documentation_link} target="_blank" rel="noopener noreferrer" style={{marginLeft: '0.5rem', color: '#646cff', fontSize: '0.85rem'}}>
                                      📚 Docs
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Traditional Recommendations (if no LLM) */}
                      {!postMortemResults.llm_analysis && postMortemResults.recommendations && postMortemResults.recommendations.length > 0 && (
                        <div className="breakdown" style={{marginTop: '1rem', paddingTop: '1rem'}}>
                          <strong>Top Recommendations:</strong>
                          {postMortemResults.recommendations.slice(0, 3).map((rec, i) => (
                            <p key={i} style={{fontSize: '0.9rem', marginTop: '0.5rem'}}>• {rec}</p>
                          ))}
                        </div>
                      )}

                      {postMortemResults.summary.total_errors === 0 && postMortemResults.summary.total_warnings === 0 && (
                        <p className="success-message">🎉 No incidents found!</p>
                      )}
                    </>
                  )}
                  
                  {postMortemResults.scan_id && (
                    <p className="info-message">✅ Saved to history (ID: {postMortemResults.scan_id})</p>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Info Panel */}
          <div className="info-panel">
            <h2>📊 Platform Overview</h2>
            
            <div className="info-section">
              <h3>💀 Zombie Hunter 🤖</h3>
              <p>Identifies idle EC2 instances and unused resources. <strong>ML-powered predictions</strong> flag resources at risk of becoming zombies before they waste money.</p>
            </div>

            <div className="info-section">
              <h3>📏 Right-Sizing 🤖</h3>
              <p>Analyzes CPU and memory usage with <strong>LSTM neural networks</strong> to forecast workload patterns and recommend optimal instance types proactively.</p>
            </div>

            <div className="info-section">
              <h3>🔒 Compliance 🤖</h3>
              <p>Scans for security violations with <strong>ML anomaly detection</strong> to catch unusual configurations that rules might miss.</p>
            </div>

            <div className="info-section">
              <h3>📋 Post-Mortem 🤖</h3>
              <p>Analyzes CloudWatch Logs with <strong>AI-powered root cause analysis</strong> using Claude API for intelligent insights and recommendations.</p>
            </div>
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