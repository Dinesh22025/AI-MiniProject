import { useEffect, useState } from 'react'
import api from './api'

export default function HistoryPage() {
  const [history, setHistory] = useState([])
  const [meta, setMeta] = useState({ total: 0, limit: 0, overLimit: false })
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      setLoading(true)
      const { data } = await api.get('/history')
      setHistory(data.items)
      setMeta({ total: data.total, limit: data.limit, overLimit: data.overLimit })
    } catch (error) {
      console.error('Failed to load history:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // Auto-refresh every 10 seconds
    const interval = setInterval(load, 10000)
    return () => clearInterval(interval)
  }, [])

  const clear = async () => {
    if (confirm('Are you sure you want to clear all history?')) {
      await api.delete('/history/clear')
      load()
    }
  }

  const getEventColor = (eventType) => {
    switch (eventType) {
      case 'drowsy': return '#e74c3c'
      case 'yawning': return '#e67e22'
      case 'distracted': return '#f39c12'
      default: return '#95a5a6'
    }
  }

  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'drowsy': return '😴'
      case 'yawning': return '🥱'
      case 'distracted': return '👀'
      default: return '⚠️'
    }
  }

  if (loading) {
    return <div><h2>Detection History</h2><p>Loading...</p></div>
  }

  return (
    <div>
      <h2>Detection History</h2>
      <div style={{marginBottom: '20px'}}>
        <p>Total alerts recorded: <strong>{meta.total}</strong> / {meta.limit}</p>
        {meta.overLimit && <p className="warning">⚠️ History limit reached. Older records are automatically removed.</p>}
        <button onClick={clear} style={{marginRight: '10px'}}>Clear All History</button>
        <button onClick={load}>Refresh</button>
      </div>
      
      {history.length === 0 ? (
        <div className="card">
          <p>No alert events recorded yet. Start monitoring to see detection history.</p>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Event Type</th>
              <th>Confidence</th>
              <th>Details</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item) => (
              <tr key={item.id}>
                <td>
                  <span style={{color: getEventColor(item.eventType)}}>
                    {getEventIcon(item.eventType)} {item.eventType.toUpperCase()}
                  </span>
                </td>
                <td><strong>{(item.confidence * 100).toFixed(1)}%</strong></td>
                <td style={{fontSize: '12px'}}>
                  Head: {item.meta?.head_tilt || 0}° | 
                  Gaze: {item.meta?.gaze_offset || 0}% | 
                  Faces: {item.meta?.faces || 0}
                  {item.meta?.ear && <><br/>EAR: {item.meta.ear} | MAR: {item.meta.mar}</>}
                </td>
                <td>{new Date(item.timestamp).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
