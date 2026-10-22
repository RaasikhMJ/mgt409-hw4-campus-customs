import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/session'

export function CreateAccountPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    document.title = 'Create Account · Campus Customs'
  }, [])

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const password = String(form.get('password') ?? '')
    const confirmPassword = String(form.get('confirmPassword') ?? '')
    if (password !== confirmPassword) {
      setError('Those passwords do not match.')
      return
    }
    setBusy(true)
    setError('')
    try {
      await register({
        firstName: String(form.get('firstName') ?? ''),
        lastName: String(form.get('lastName') ?? ''),
        email: String(form.get('email') ?? ''),
        password,
        confirmPassword,
      })
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
        <p className="kicker">New to the floor</p>
        <h1>Create an account.</h1>
        <div className="split-fields">
          <label>
            First name
            <input name="firstName" autoComplete="given-name" required />
          </label>
          <label>
            Last name
            <input name="lastName" autoComplete="family-name" required />
          </label>
        </div>
        <label>
          Email
          <input name="email" type="email" autoComplete="email" required />
        </label>
        <label>
          Password
          <input name="password" type="password" autoComplete="new-password" required minLength={8} />
        </label>
        <label>
          Confirm password
          <input
            name="confirmPassword"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
          />
        </label>
        <button className="btn btn-brass" type="submit" disabled={busy}>
          {busy ? 'Saving…' : 'Create account'}
        </button>
        {error && <p className="form-error">{error}</p>}
        <p className="form-switch">
          Already on the list? <Link to="/login">Log in</Link>
        </p>
      </form>
    </section>
  )
}
