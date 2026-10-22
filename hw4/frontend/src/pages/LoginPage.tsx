import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/session'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    document.title = 'Log In · Campus Customs'
  }, [])

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setBusy(true)
    setError('')
    try {
      await login(String(form.get('email') ?? ''), String(form.get('password') ?? ''))
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The counter did not answer.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="page auth">
      <form className="auth-card" onSubmit={onSubmit}>
        <p className="kicker">Welcome back</p>
        <h1>Log in.</h1>
        <label>
          Email
          <input name="email" type="email" autoComplete="email" required />
        </label>
        <label>
          Password
          <input name="password" type="password" autoComplete="current-password" required />
        </label>
        <button className="btn btn-brass" type="submit" disabled={busy}>
          {busy ? 'Checking…' : 'Enter'}
        </button>
        {error && <p className="form-error">{error}</p>}
        <p className="form-switch">
          New here? <Link to="/create-account">Create an account</Link>
        </p>
      </form>
    </section>
  )
}
