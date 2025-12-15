import { useState } from 'react'
import './App.css'

function App() {
  const [apiStatus, setApiStatus] = useState<string>('Checking...')

  // Test API connection
  const checkAPI = async () => {
    try {
      const response = await fetch('http://localhost:8000/')
      const data = await response.json()
      setApiStatus(`✅ Connected: ${data.message}`)
    } catch (error) {
      setApiStatus('❌ API not reachable')
    }
  }

  return (
    <div className="App">
      <h1>CloudSense Platform</h1>
      <p>Unified AWS Cost Optimization Suite</p>
      
      <button onClick={checkAPI}>Test API Connection</button>
      <p>{apiStatus}</p>

      <div className="service-grid">
        <div className="service-card">
          <h2>💀 Zombie Resource Hunter</h2>
          <p>Find and eliminate unused AWS resources</p>
          <button>Run Scan</button>
        </div>

        <div className="service-card">
          <h2>📏 Right-Sizing Engine</h2>
          <p>Optimize instance types based on usage</p>
          <button>Analyze Resources</button>
        </div>
      </div>
    </div>
  )
}

export default App
