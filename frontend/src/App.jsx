import { useState, useEffect } from 'react'
import InputPanel from './components/InputPanel'
import ScopeDoc from './components/ScopeDoc'
import Header from './components/Header'
import './App.css'

const API_URL = (import.meta.env.VITE_API_URL || 'https://quoteshield.onrender.com').replace(/\/$/, '')

export default function App() {
  const [scope, setScope] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Wake the Render free-tier server while the user is still typing
  useEffect(() => {
    fetch(`${API_URL}/`).catch(() => {})
  }, [])

  async function handleGenerate(description, context) {
    setLoading(true)
    setError(null)
    setScope(null)

    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 90000)

    try {
      let res
      try {
        res = await fetch(`${API_URL}/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ description, context }),
          signal: controller.signal,
        })
      } catch (e) {
        if (e.name === 'AbortError') throw new Error('The server took too long. Please try again.')
        throw new Error('Server is waking up (free hosting sleeps when idle). Give it 30 seconds and try again.')
      }

      let body = null
      try { body = await res.json() } catch { /* non-JSON error page */ }

      if (!res.ok) {
        const detail = typeof body?.detail === 'string' ? body.detail : null
        throw new Error(detail || `Server error (${res.status}). Please try again.`)
      }
      if (!body || !Array.isArray(body.deliverables)) {
        throw new Error('Got an unexpected response. Please try again.')
      }
      setScope(body)
    } catch (e) {
      setError(e.message)
    } finally {
      clearTimeout(timer)
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <Header />
      <main className="main">
        {!scope ? (
          <InputPanel onGenerate={handleGenerate} loading={loading} error={error} />
        ) : (
          <ScopeDoc data={scope} onReset={() => { setScope(null); setError(null) }} />
        )}
      </main>
    </div>
  )
}
