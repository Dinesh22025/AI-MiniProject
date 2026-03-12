import { useState } from 'react'
import api from './api'

export default function SettingsPage({ user, onUserUpdate }) {
  const [form, setForm] = useState({
    language: user.language,
    alertVolume: user.alertVolume,
    theme: user.theme,
  })
  const [status, setStatus] = useState('')

  const save = async () => {
    const { data } = await api.put('/settings', form)
    onUserUpdate(data.user)
    setStatus('Settings saved')
  }

  return (
    <div>
      <h2>Settings</h2>
      <div className="settings-grid">
        <label>
          Language
          <select value={form.language} onChange={(e) => setForm({ ...form, language: e.target.value })}>
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="hi">Hindi</option>
          </select>
        </label>
        <label>
          Alert Volume ({form.alertVolume}%)
          <input
            type="range"
            min="10"
            max="100"
            value={form.alertVolume}
            onChange={(e) => setForm({ ...form, alertVolume: Number(e.target.value) })}
          />
        </label>
        <label>
          Theme
          <select value={form.theme} onChange={(e) => setForm({ ...form, theme: e.target.value })}>
            <option value="dark">Dark</option>
            <option value="light">Light</option>
          </select>
        </label>
      </div>
      <button onClick={save}>Save Settings</button>
      {status && <p>{status}</p>}
    </div>
  )
}
