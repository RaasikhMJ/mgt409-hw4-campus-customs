import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { swagRating } from '../data/format'
import { money, type Product } from '../data/types'
import { SwagRating } from './SwagRating'

export function PieceStage({
  product,
  backTo = '/products',
  backLabel = 'All products',
  kicker,
  children,
}: {
  product: Product
  backTo?: string
  backLabel?: string
  kicker?: string
  children?: ReactNode
}) {
  return (
    <article className="stage">
      <div className="stage-photo">
        <img src={product.image} alt={product.name} />
      </div>
      <div className="stage-copy">
        <Link className="back" to={backTo}>
          {backLabel}
        </Link>
        <p className="eyebrow">{kicker || product.garmentType}</p>
        <h1>{product.name}</h1>
        <SwagRating score={swagRating(product)} />
        <p className="stage-price">{money(product.price)}</p>
        <p className="description">{product.description}</p>
        {product.colors.length > 0 && (
          <p className="colors">
            <span>Colors</span>
            {product.colors.join(' · ')}
          </p>
        )}
        <h2>Sizes and stock</h2>
        <ul className="sizes">
          {product.sizes.map((item) => (
            <li key={item.size} className={item.quantity === 0 ? 'is-out' : ''}>
              <span>{item.size}</span>
              <span>{item.quantity === 0 ? 'Out' : `${item.quantity} in stock`}</span>
            </li>
          ))}
        </ul>
        {children}
      </div>
    </article>
  )
}
