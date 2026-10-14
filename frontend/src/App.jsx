import { useState } from 'react'
import InputPanel from './components/InputPanel'
import ScopeDoc from './components/ScopeDoc'
import Header from './components/Header'
import './App.css'

export default function App() {
  const [scope, setScope] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleGenerate(description, context) {
    setLoading(true)
    setError(null)
    setScope(null)

    try {
      const res = await fetch('https://quoteshield.onrender.com/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, context }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Server error')
      }
      const data = await res.json()
      setScope(data)
    } catch (e) {
      setError(e.message)
    } finally {
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
