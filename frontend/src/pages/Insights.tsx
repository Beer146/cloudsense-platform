import { useState, useEffect } from 'react'
import './Insights.css'

interface InsightsData {
  overall_health: {
    score: number
    breakdown: {
      cost_efficiency: number
      right_sizing: number
      security: number
    }
  }
  current_state: {
    monthly_waste: number
    annual_savings_opportunity: number
    critical_violations: number
    total_violations: number
  }
  trends_30d: {
    zombie_cost: {
      current: number
      previous: number
      change: number
      improving: boolean
    }
    compliance: {
      current: number
      previous: number
      change: number
      improving: boolean
    }
  }
  top_recommendations: Array<{
    priority: number
    type: string
    title: string
    description: string
    impact: string
    effort: string
    action: string
  }>
  last_updated: string
}

function Insights() {
  const [insights, setInsights] = useState<InsightsData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadInsights()
  }, [])

  const loadInsights = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/insights/summary')
      const data = await response.json()
      setInsights(data)
    } catch (error) {
      console.error('Failed to load insights:', error)
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#42d392'
    if (score >= 60) return '#ffd93d'
    if (score >= 40) return '#ffa500'
    return '#ff6b6b'
  }

  const getTypeIcon = (type: string) => {
    switch(type) {
      case 'security': return '🔒'
      case 'cost': return '💰'
      case 'optimization': return '📊'
      default: return '•'
    }
  }

  const getTypeBadgeColor = (type: string) => {
    switch(type) {
      case 'security': return '#ff6b6b'
      case 'cost': return '#ffa500'
      case 'optimization': return '#42d392'
      default: return '#646cff'
    }
  }

  if (loading) {
    return (
      <div className="insights-page">
        <div className="insights-header">
          <h1>✨ Insights</h1>
        </div>
        <div className="loading-state">
          <p>Analyzing your AWS environment...</p>
        </div>
      </div>
    )
  }

  if (!insights) {
    return (
      <div className="insights-page">
        <div className="insights-header">
          <h1>✨ Insights</h1>
        </div>
        <div className="empty-state">
          <p>No data available. Run some scans to generate insights!</p>
        </div>
      </div>
    )
  }

  return (
    <div className="insights-page">
      <div className="insights-header">
        <h1>✨ Insights</h1>
        <button className="refresh-btn" onClick={loadInsights}>
          🔄 Refresh
        </button>
      </div>

      {/* Overall Health Score */}
      <div className="health-score-section">
        <div className="main-score">
          <h2>Overall AWS Health</h2>
          <div className="score-circle" style={{ borderColor: getScoreColor(insights.overall_health.score) }}>
            <span className="score-number" style={{ color: getScoreColor(insights.overall_health.score) }}>
              {insights.overall_health.score}
            </span>
            <span className="score-label">/100</span>
          </div>
        </div>

        <div className="score-breakdown">
          <div className="score-item">
            <div className="score-bar">
              <div 
                className="score-fill" 
                style={{ 
                  width: `${insights.overall_health.breakdown.cost_efficiency}%`,
                  background: getScoreColor(insights.overall_health.breakdown.cost_efficiency)
                }}
              />
            </div>
            <div className="score-info">
              <span className="score-name">💰 Cost Efficiency</span>
              <span className="score-value">{insights.overall_health.breakdown.cost_efficiency}/100</span>
            </div>
          </div>

          <div className="score-item">
            <div className="score-bar">
              <div 
                className="score-fill" 
                style={{ 
                  width: `${insights.overall_health.breakdown.right_sizing}%`,
                  background: getScoreColor(insights.overall_health.breakdown.right_sizing)
                }}
              />
            </div>
            <div className="score-info">
              <span className="score-name">📏 Right-Sizing</span>
              <span className="score-value">{insights.overall_health.breakdown.right_sizing}/100</span>
            </div>
          </div>

          <div className="score-item">
            <div className="score-bar">
              <div 
                className="score-fill" 
                style={{ 
                  width: `${insights.overall_health.breakdown.security}%`,
                  background: getScoreColor(insights.overall_health.breakdown.security)
                }}
              />
            </div>
            <div className="score-info">
              <span className="score-name">🔒 Security</span>
              <span className="score-value">{insights.overall_health.breakdown.security}/100</span>
            </div>
          </div>
        </div>
      </div>

      {/* Current State */}
      <div className="current-state-section">
        <h2>Current State</h2>
        <div className="state-grid">
          <div className="state-card">
            <span className="state-icon">💸</span>
            <span className="state-value">${insights.current_state.monthly_waste.toFixed(2)}</span>
            <span className="state-label">Monthly Waste</span>
          </div>
          <div className="state-card">
            <span className="state-icon">💰</span>
            <span className="state-value">${insights.current_state.annual_savings_opportunity.toFixed(2)}</span>
            <span className="state-label">Annual Savings Opportunity</span>
          </div>
          <div className="state-card">
            <span className="state-icon">🚨</span>
            <span className="state-value">{insights.current_state.critical_violations}</span>
            <span className="state-label">Critical Violations</span>
          </div>
          <div className="state-card">
            <span className="state-icon">⚠️</span>
            <span className="state-value">{insights.current_state.total_violations}</span>
            <span className="state-label">Total Violations</span>
          </div>
        </div>
      </div>

      {/* Trends */}
      <div className="trends-section">
        <h2>30-Day Trends</h2>
        <div className="trends-grid">
          <div className="trend-card">
            <div className="trend-header">
              <span className="trend-icon">💀</span>
              <span className="trend-title">Zombie Cost</span>
            </div>
            <div className="trend-values">
              <div className="trend-current">
                <span className="trend-label">Current</span>
                <span className="trend-number">${insights.trends_30d.zombie_cost.current.toFixed(2)}</span>
              </div>
              <div className="trend-arrow">
                {insights.trends_30d.zombie_cost.improving ? '→' : '←'}
              </div>
              <div className="trend-previous">
                <span className="trend-label">30 Days Ago</span>
                <span className="trend-number">${insights.trends_30d.zombie_cost.previous.toFixed(2)}</span>
              </div>
            </div>
            <div className={`trend-status ${insights.trends_30d.zombie_cost.improving ? 'improving' : 'worsening'}`}>
              {insights.trends_30d.zombie_cost.improving ? '✅ Improving' : '⚠️ Worsening'}
              {insights.trends_30d.zombie_cost.change !== 0 && (
                <span className="trend-change">
                  {insights.trends_30d.zombie_cost.improving ? '' : '+'}
                  ${Math.abs(insights.trends_30d.zombie_cost.change).toFixed(2)}
                </span>
              )}
            </div>
          </div>

          <div className="trend-card">
            <div className="trend-header">
              <span className="trend-icon">🔒</span>
              <span className="trend-title">Security Violations</span>
            </div>
            <div className="trend-values">
              <div className="trend-current">
                <span className="trend-label">Current</span>
                <span className="trend-number">{insights.trends_30d.compliance.current}</span>
              </div>
              <div className="trend-arrow">
                {insights.trends_30d.compliance.improving ? '→' : '←'}
              </div>
              <div className="trend-previous">
                <span className="trend-label">30 Days Ago</span>
                <span className="trend-number">{insights.trends_30d.compliance.previous}</span>
              </div>
            </div>
            <div className={`trend-status ${insights.trends_30d.compliance.improving ? 'improving' : 'worsening'}`}>
              {insights.trends_30d.compliance.improving ? '✅ Improving' : '⚠️ Worsening'}
              {insights.trends_30d.compliance.change !== 0 && (
                <span className="trend-change">
                  {insights.trends_30d.compliance.improving ? '' : '+'}
                  {Math.abs(insights.trends_30d.compliance.change)}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Top Recommendations */}
      <div className="recommendations-section">
        <h2>🎯 Top Recommendations</h2>
        {insights.top_recommendations.length === 0 ? (
          <div className="empty-recommendations">
            <p>🎉 Great job! No urgent recommendations at this time.</p>
          </div>
        ) : (
          <div className="recommendations-list">
            {insights.top_recommendations.map((rec, index) => (
              <div key={index} className="recommendation-card">
                <div className="rec-header">
                  <span className="rec-icon">{getTypeIcon(rec.type)}</span>
                  <span className="rec-type" style={{ background: getTypeBadgeColor(rec.type) }}>
                    {rec.type}
                  </span>
                  <span className="rec-priority">Priority {rec.priority}</span>
                </div>
                <h3 className="rec-title">{rec.title}</h3>
                <p className="rec-description">{rec.description}</p>
                <div className="rec-details">
                  <span className="rec-impact">💡 {rec.impact}</span>
                  <span className="rec-effort">⏱️ {rec.effort}</span>
                </div>
                <div className="rec-action">
                  <strong>Action:</strong> {rec.action}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="last-updated">
        Last updated: {new Date(insights.last_updated).toLocaleString()}
      </div>
    </div>
  )
}

export default Insights
