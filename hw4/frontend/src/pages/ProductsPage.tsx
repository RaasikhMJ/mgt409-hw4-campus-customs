import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { SwagRating } from '../components/SwagRating'
import { loadProducts } from '../data/shop'
import { shortDescription, swagRating } from '../data/format'
import { LANES, laneOf, money, type Lane, type Product } from '../data/types'

export function ProductsPage() {
  const [lane, setLane] = useState<Lane>('All')
  const [query, setQuery] = useState('')
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    document.title = 'Products · Campus Customs'
    let live = true
    loadProducts()
      .then((items) => {
        if (live) setProducts(items)
      })
      .catch(() => {
        if (live) setError('The rack is quiet. Start the shop API and refresh.')
      })
    return () => {
      live = false
    }
  }, [])

  const visible = useMemo(() => {
    const rack = products ?? []
    const inLane = lane === 'All' ? rack : rack.filter((item) => laneOf(item.garmentType) === lane)
    const needle = query.trim().toLowerCase()
    if (!needle) return inLane
    return inLane.filter((item) => {
      const hay = [item.name, item.garmentType, item.description, ...item.colors]
        .join(' ')
        .toLowerCase()
      return hay.includes(needle)
    })
  }, [lane, products, query])

  return (
    <section className="page rack-page">
      <header className="section-head">
        <p className="kicker">The rack · {products ? `${products.length} pieces` : '…'}</p>
        <h1>What the shop actually has.</h1>
        <p className="deck">
          Photos, names, and prices come from the shop API, which reads the
          Campus Customs catalogue. Swag is a 1–5 read of the piece — graphics,
          color, and cut — not a separate column in the book.
        </p>
      </header>
      {error && <p className="status">{error}</p>}
      {!error && !products && <p className="status">Opening the rack…</p>}
      <form className="rack-tools" role="search" onSubmit={(event) => event.preventDefault()}>
        <label htmlFor="rack-search">Find a piece</label>
        <input
          id="rack-search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Name, color, or cut"
          autoComplete="off"
        />
        <p className="rack-count">{products ? `${visible.length} on the glass` : '…'}</p>
      </form>
      <div className="filters" role="group" aria-label="Garment type">
        {LANES.map((item) => (
          <button
            key={item}
            type="button"
            className={item === lane ? 'is-on' : ''}
            aria-pressed={item === lane}
            onClick={() => setLane(item)}
          >
            {item}
          </button>
        ))}
      </div>
      {products && visible.length === 0 && (
        <p className="rack-empty">Nothing in this cut matches that search.</p>
      )}
      <ul className="rack">
        {visible.map((product) => (
          <li key={product.productId}>
            <Link className="card" to={`/products/${product.productId}`}>
              <div className="card-photo">
                <img src={product.image} alt="" />
              </div>
              <div className="card-body">
                <h2>{product.name}</h2>
                <p className="price">{money(product.price)}</p>
                <p className="blurb">{shortDescription(product.description)}</p>
                <SwagRating score={swagRating(product)} />
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}
