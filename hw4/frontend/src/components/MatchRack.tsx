import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { money } from '../data/types'
import { useMatches } from '../rack/matches'

export function MatchRack() {
  const { query, products, searching, clear } = useMatches()
  const railRef = useRef<HTMLElement>(null)
  const visible = products.length > 0 || searching

  useEffect(() => {
    if (!visible) return
    railRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [visible, products, searching])

  if (!visible) return null

  return (
    <section className="match-rack" ref={railRef} aria-live="polite">
      <header className="match-head">
        <div>
          <p className="kicker">Pulled for the night</p>
          <h2>{searching && products.length === 0 ? 'Checking the rack.' : 'On the glass.'}</h2>
          {query && <p className="match-ask">“{query}”</p>}
        </div>
        <div className="match-meta">
          <p>{searching ? 'Pulling pieces…' : `${products.length} pieces`}</p>
          {products.length > 0 && (
            <button type="button" onClick={clear}>
              Clear
            </button>
          )}
        </div>
      </header>
      <ul className="match-rail">
        {products.map((product, index) => (
          <li key={product.productId}>
            <Link className="match-card" to={`/products/${product.productId}`}>
              <div className="match-photo">
                <span>{String(index + 1).padStart(2, '0')}</span>
                <img src={product.image} alt={product.name} />
              </div>
              <div className="match-copy">
                <h3>{product.name}</h3>
                <p className="match-price">{money(product.price)}</p>
                <p className="match-blurb">{product.blurb}</p>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}
