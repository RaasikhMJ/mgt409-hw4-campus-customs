import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

export type Shopper = {
  id: number
  firstName: string
  lastName: string
  email: string
  name: string
}

type RegisterInput = {
  firstName: string
  lastName: string
  email: string
  password: string
  confirmPassword: string
}

type AuthValue = {
  shopper: Shopper | null
  ready: boolean
  register: (input: RegisterInput) => Promise<Shopper>
  login: (email: string, password: string) => Promise<Shopper>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthValue | null>(null)

async function readError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string }
    if (payload.detail) return payload.detail
  } catch {
    /* The counter sent something that was not JSON. */
  }
  return 'The counter did not answer.'
}

async function postShopper(path: string, body: unknown): Promise<Shopper> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<Shopper>
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [shopper, setShopper] = useState<Shopper | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let live = true
    fetch('/api/me', { credentials: 'include' })
      .then(async (response) => {
        if (!response.ok) return null
        return response.json() as Promise<Shopper>
      })
      .then((person) => {
        if (live) setShopper(person)
      })
      .finally(() => {
        if (live) setReady(true)
      })
    return () => {
      live = false
    }
  }, [])

  async function register(input: RegisterInput) {
    const person = await postShopper('/api/register', input)
    setShopper(person)
    return person
  }

  async function login(email: string, password: string) {
    const person = await postShopper('/api/login', { email, password })
    setShopper(person)
    return person
  }

  async function logout() {
    await fetch('/api/logout', { method: 'POST', credentials: 'include' })
    setShopper(null)
  }

  return (
    <AuthContext.Provider value={{ shopper, ready, register, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must sit inside AuthProvider')
  return value
}
