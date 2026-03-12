import { useEffect, useRef, useState } from 'react'
import api from './api'

export default function DashboardPage() {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const audioContextRef = useRef(null)
  const alertIntervalRef = useRef(null)
  const [analysis, setAnalysis] = useState(null)
  const [alert, setAlert] = useState(null)
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isAlertActive, setIsAlertActive] = useState(false)

  useEffect(() => {
    const startCamera = async () => {
      try {
        const constraints = {
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'user'
          }
        }
        const stream = await navigator.mediaDevices.getUserMedia(constraints)
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.play().catch(err => console.error('Video play error:', err))
        }
      } catch (err) {
        console.error('Camera access denied or failed:', err)
        alert('Camera access is required. Please allow camera permission.')
      }
    }
    startCamera()
    
    return () => {
      if (videoRef.current?.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  // Create continuous alert sound
  const createContinuousAlert = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
    }
    const ctx = audioContextRef.current
    
    // Create oscillator for beep sound
    const oscillator = ctx.createOscillator()
    const gainNode = ctx.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(ctx.destination)
    
    // High-pitched urgent beep
    oscillator.frequency.setValueAtTime(1000, ctx.currentTime)
    oscillator.frequency.setValueAtTime(800, ctx.currentTime + 0.1)
    oscillator.frequency.setValueAtTime(1000, ctx.currentTime + 0.2)
    
    // Loud volume
    gainNode.gain.setValueAtTime(0.6, ctx.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3)
    
    oscillator.start(ctx.currentTime)
    oscillator.stop(ctx.currentTime + 0.3)
  }

  // Start continuous alert
  const startContinuousAlert = () => {
    if (alertIntervalRef.current) return // Already running
    
    setIsAlertActive(true)
    createContinuousAlert() // First beep immediately
    
    // Continue beeping every 800ms
    alertIntervalRef.current = setInterval(() => {
      createContinuousAlert()
    }, 800)
  }

  // Stop continuous alert
  const stopContinuousAlert = () => {
    if (alertIntervalRef.current) {
      clearInterval(alertIntervalRef.current)
      alertIntervalRef.current = null
    }
    setIsAlertActive(false)
  }

  useEffect(() => {
    const analyzeFrame = async () => {
      if (!videoRef.current || !canvasRef.current || isAnalyzing) return
      
      if (videoRef.current.readyState !== videoRef.current.HAVE_ENOUGH_DATA) {
        return
      }
      
      setIsAnalyzing(true)
      
      try {
        const ctx = canvasRef.current.getContext('2d')
        const width = videoRef.current.videoWidth
        const height = videoRef.current.videoHeight
        
        if (width === 0 || height === 0) {
          setIsAnalyzing(false)
          return
        }
        
        canvasRef.current.width = width
        canvasRef.current.height = height
        ctx.drawImage(videoRef.current, 0, 0, width, height)
        
        const frame = canvasRef.current.toDataURL('image/jpeg', 0.7)
        const { data } = await api.post('/monitor/analyze', { frame })
        
        setAnalysis(data.analysis)
        setAlert(data.alert)
        
        // Handle continuous alert based on status
        if (data.alert?.active && (data.analysis.status === 'drowsy' || data.analysis.status === 'distracted' || data.analysis.status === 'yawning')) {
          setSecondsLeft(data.alert.durationSeconds)
          if (!isAlertActive) {
            startContinuousAlert()
          }
        } else if (data.analysis.status === 'focused') {
          // Stop alert when driver is focused
          stopContinuousAlert()
          setSecondsLeft(0)
        }
      } catch (err) {
        console.error('Frame analysis error:', err)
      } finally {
        setIsAnalyzing(false)
      }
    }

    const interval = setInterval(analyzeFrame, 1000) // Faster analysis - every 1 second
    return () => clearInterval(interval)
  }, [isAnalyzing])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopContinuousAlert()
    }
  }, [])

  useEffect(() => {
    if (secondsLeft <= 0) return
    const timer = setInterval(() => setSecondsLeft((prev) => prev - 1), 1000)
    return () => clearInterval(timer)
  }, [secondsLeft])

  return (
    <div>
      <h2>Live Driver Dashboard</h2>
      <div className="grid">
        <div className="card">
          <video 
            ref={videoRef} 
            autoPlay 
            playsInline
            muted 
            className="video"
            style={{ width: '100%', height: 'auto', backgroundColor: '#000' }}
          />
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>
        <div className="card">
          <h3>Real-time Status</h3>
          <p>Status: <strong style={{color: analysis?.status === 'focused' ? 'green' : analysis?.status === 'drowsy' ? 'red' : analysis?.status === 'distracted' ? 'orange' : analysis?.status === 'yawning' ? 'red' : 'gray'}}>{analysis?.status || 'Initializing...'}</strong></p>
          <p>Confidence: <strong>{analysis?.confidence ? (analysis.confidence * 100).toFixed(1) + '%' : '0%'}</strong></p>
          <p>Head Tilt: <strong>{analysis?.head_tilt ?? 0}°</strong></p>
          <p>Gaze Offset: <strong>{analysis?.gaze_offset ?? 0}%</strong></p>
          <p>Faces Detected: <strong>{analysis?.faces ?? 0}</strong></p>
          <p>Eye Aspect Ratio: <strong>{analysis?.ear ?? 0}</strong></p>
          <p>Mouth Aspect Ratio: <strong>{analysis?.mar ?? 0}</strong></p>
          <p>Analysis: <strong>{isAnalyzing ? 'Processing...' : 'Ready'}</strong></p>
          <div style={{marginTop: '10px', fontSize: '12px', color: '#bbb'}}>
            <p>• EAR &lt; 0.25 = Drowsy | MAR &gt; 0.08 + Eyes Open = Yawn</p>
            <p>• Gaze &gt; 8% or Tilt &gt; 7% = Distracted</p>
            <p>• Priority: Drowsy → Distracted → Yawning → Focused</p>
          </div>
          {alert?.active && (
            <div className="alert-box" style={{backgroundColor: isAlertActive ? '#d32f2f' : '#922b21'}}>
              <p><strong>{alert.message}</strong></p>
              <p>🚨 CONTINUOUS ALERT ACTIVE: {secondsLeft}s</p>
              <p style={{fontSize: '12px'}}>Alert will stop when you return to focused state</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
