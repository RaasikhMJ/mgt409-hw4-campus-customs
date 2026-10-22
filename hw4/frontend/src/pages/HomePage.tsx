import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useBag } from '../cart/bag'
import { BagIcon } from '../components/BagIcon'
import { SwagRating } from '../components/SwagRating'
import { loadProducts } from '../data/shop'
import { shortDescription, swagRating } from '../data/format'
import { laneOf, money, type Product } from '../data/types'

const FEATURED_LANES = ['Hoodies', 'Crews', 'Tees'] as const

function pickFeatured(products: Product[]): Product[] {
  return FEATURED_LANES.flatMap((lane) => {
    const found = products.find((item) => laneOf(item.garmentType) === lane)
    return found ? [found] : []
  })
}

export function HomePage() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState('')
  const bag = useBag()

  useEffect(() => {
    document.title = 'Campus Customs'
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

  const featured = products ? pickFeatured(products) : []

  return (
    <div className="home">
      <section className="hero">
        <p className="kicker">Campus Customs · Broadway</p>
        <h1>
          The crest, <em>off duty.</em>
        </h1>
        <p className="deck">
          Yale gear from the shop across from campus. Same pride as the
          daylight Bulldog Blue rack, cut closer for New Haven after class.
        </p>
        <div className="hero-actions">
          <Link className="btn btn-brass" to="/products">
            Shop the rack
          </Link>
          <Link className="btn btn-ghost" to="/about">
            About the house
          </Link>
          <Link className="bag-logo" to="/cart" aria-label="Open the bag">
            <BagIcon />
            <span>{bag.count > 0 ? `Bag · ${bag.count}` : 'Bag'}</span>
          </Link>
        </div>
      </section>
      <section className="band">
        <p>Hoodies</p>
        <p>Crews</p>
        <p>The Game</p>
        <p>Quarter-zips</p>
        <p>After hours</p>
      </section>
      <section className="feature">
        <header className="section-head">
          <p className="kicker">On the floor</p>
          <h2>Three ways off the quad.</h2>
        </header>
        {error && <p className="status">{error}</p>}
        {!error && !products && <p className="status">Opening the rack…</p>}
        <ul className="feature-grid">
          {featured.map((product) => (
            <li key={product.productId}>
              <Link className="card" to={`/products/${product.productId}`}>
                <div className="card-photo">
                  <img src={product.image} alt={product.name} />
                </div>
                <div className="card-body">
                  <p className="eyebrow">{laneOf(product.garmentType)}</p>
                  <h3>{product.name}</h3>
                  <p className="price">{money(product.price)}</p>
                  <p className="blurb">{shortDescription(product.description)}</p>
                  <SwagRating score={swagRating(product)} />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
