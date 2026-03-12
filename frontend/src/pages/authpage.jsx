import { useState } from 'react'
import api from './api'

export default function AuthPage({ onAuthenticated }) {
  const [isSignup, setIsSignup] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')

  console.log('AuthPage rendering')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const endpoint = isSignup ? '/auth/signup' : '/auth/login'
      const payload = isSignup ? form : { email: form.email, password: form.password }
      const { data } = await api.post(endpoint, payload)
      onAuthenticated(data.token, data.user)
    } catch (err) {
      setError(err.response?.data?.error || 'Authentication failed')
    }
  }

  return (
    <div className="auth-wrapper">
      <h1 style={{color: 'white'}}>Welcome to Ai copilot</h1>
      <form className="auth-card" onSubmit={submit}>
        <h2>{isSignup ? 'Sign Up' : 'Login'}</h2>
        {isSignup && (
          <input
            placeholder="Full Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
        )}
        <input
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        {error && <p className="error">{error}</p>}
        <button type="submit">{isSignup ? 'Create account' : 'Login'}</button>
        <p>
          {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button type="button" className="link" onClick={() => setIsSignup((s) => !s)}>
            {isSignup ? 'Login' : 'Sign up'}
          </button>
        </p>
      </form>
    </div>
  )
}
