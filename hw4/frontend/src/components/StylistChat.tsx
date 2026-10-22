import { useEffect, useId, useRef, useState, type FormEvent } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../auth/session'
import { askStylist, type StylistMatch, type StylistTurn } from '../chat/stylist'
import { useMatches } from '../rack/matches'
import goldieBadge from '../assets/goldie-badge.png'

const GREETING: StylistTurn = {
  role: 'stylist',
  content:
    'Swag stylist, on the glass. Ask what crew necks, hoodies, or tees are on the rack and I will pull the real pieces.',
}

function openProductId(pathname: string): string {
  const match = pathname.match(/^\/products\/([^/]+)$/)
  return match ? decodeURIComponent(match[1]) : ''
}

export function StylistChat() {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [turns, setTurns] = useState<StylistTurn[]>([GREETING])
  const listRef = useRef<HTMLDivElement>(null)
  const inputId = useId()
  const matches = useMatches()
  const showRef = useRef(matches.show)
  const clearRef = useRef(matches.clear)
  const hadShopper = useRef(false)
  showRef.current = matches.show
  clearRef.current = matches.clear
  const { shopper, ready } = useAuth()
  const { pathname } = useLocation()

  useEffect(() => {
    const list = listRef.current
    if (!list) return
    list.scrollTop = list.scrollHeight
  }, [turns, open, busy])

  useEffect(() => {
    if (!open) return
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  useEffect(() => {
    if (!ready) return
    if (!shopper) {
      if (hadShopper.current) {
        setTurns([GREETING])
        clearRef.current()
      }
      hadShopper.current = false
      return
    }
    hadShopper.current = true
    let live = true
    fetch('/api/chat', { credentials: 'include' })
      .then(async (response) => {
        if (!response.ok) return [] as Array<StylistTurn & { products?: StylistMatch[] }>
        return response.json() as Promise<Array<StylistTurn & { products?: StylistMatch[] }>>
      })
      .then((saved) => {
        if (!live) return
        if (!saved.length) {
          setTurns([GREETING])
          return
        }
        setTurns(saved.map((turn) => ({ role: turn.role, content: turn.content })))
        const last = [...saved].reverse().find((turn) => turn.products && turn.products.length > 0)
        if (last?.products) showRef.current('From your last visit', last.products)
      })
      .catch(() => {
        if (live) setTurns([GREETING])
      })
    return () => {
      live = false
    }
  }, [ready, shopper?.id])

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const message = draft.trim()
    if (!message || busy) return
    const history = [...turns, { role: 'shopper' as const, content: message }]
    setTurns(history)
    setDraft('')
    setBusy(true)
    matches.setSearching(true)
    try {
      const result = await askStylist({
        message,
        history,
        page: { path: pathname, productId: openProductId(pathname) },
      })
      matches.show(message, result.products)
      setTurns((current) => [...current, { role: 'stylist', content: result.reply }])
    } catch {
      setTurns((current) => [
        ...current,
        {
          role: 'stylist',
          content: 'The counter missed that. Send it once more.',
        },
      ])
    } finally {
      setBusy(false)
      matches.setSearching(false)
    }
  }

  return (
    <div className="stylist">
      {open && (
        <section className="stylist-panel" role="dialog" aria-label="Swag stylist">
          <header className="stylist-head">
            <div>
              <p>{shopper ? `Saved for ${shopper.name}` : 'This visit only'}</p>
              <h2>Swag stylist</h2>
            </div>
            <button type="button" onClick={() => setOpen(false)}>
              Close
            </button>
          </header>
          <div className="stylist-log" ref={listRef}>
            {turns.map((turn, index) => (
              <p key={`${turn.role}-${index}`} className={`chat-bubble turn-${turn.role}`}>
                <span>{turn.role === 'stylist' ? 'Stylist' : 'You'}</span>
                {turn.content}
              </p>
            ))}
            {busy && <p className="chat-bubble turn-stylist pending">Checking the counter…</p>}
          </div>
          <form className="stylist-form" onSubmit={onSubmit}>
            <label htmlFor={inputId}>Ask the stylist</label>
            <div>
              <input
                id={inputId}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Navy hoodie for tonight…"
                autoComplete="off"
              />
              <button type="submit" disabled={busy || draft.trim() === ''}>
                Send
              </button>
            </div>
          </form>
        </section>
      )}
      <button
        className="stylist-launcher"
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <img className="stylist-badge" src={goldieBadge} alt="" />
        <span className="stylist-label">
          <span>{open ? 'Close stylist' : 'Swag stylist'}</span>
          <span className="stylist-name">Goldie</span>
        </span>
      </button>
    </div>
  )
}
