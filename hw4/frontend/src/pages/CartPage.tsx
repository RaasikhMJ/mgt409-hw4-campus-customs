import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/session'
import { useBag, type BagLine } from '../cart/bag'
import { PieceStage } from '../components/PieceStage'
import { loyaltyScore, SwagRating } from '../components/SwagRating'
import { loadProduct } from '../data/shop'
import { money, type Product } from '../data/types'

function LineActions({
  line,
  onQuantity,
  onRemove,
  removeLabel,
}: {
  line: BagLine
  onQuantity?: (quantity: number) => void
  onRemove: () => void
  removeLabel: string
}) {
  return (
    <div className="bag-actions">
      <p className="eyebrow">
        Size {line.size}
        {line.quantity > 1 ? ` · ${line.quantity} queued` : ''}
      </p>
      {onQuantity && (
        <div className="qty">
          <button type="button" onClick={() => onQuantity(line.quantity - 1)} aria-label="Fewer">
            −
          </button>
          <span>{line.quantity}</span>
          <button type="button" onClick={() => onQuantity(line.quantity + 1)} aria-label="More">
            +
          </button>
        </div>
      )}
      <p className="stage-price">{money(line.price * line.quantity)}</p>
      <button className="btn btn-ink" type="button" onClick={onRemove}>
        {removeLabel}
      </button>
    </div>
  )
}

export function CartPage() {
  const bag = useBag()
  const { shopper } = useAuth()
  const [products, setProducts] = useState<Record<string, Product>>({})

  useEffect(() => {
    document.title = 'The bag · Campus Customs'
  }, [])

  const ids = [...bag.lines, ...bag.purchased].map((line) => line.productId).join('|')

  useEffect(() => {
    const wanted = [...new Set(ids.split('|').filter(Boolean))]
    if (wanted.length === 0) return
    let live = true
    Promise.all(wanted.map(async (id) => [id, await loadProduct(id)] as const))
      .then((pairs) => {
        if (!live) return
        const next: Record<string, Product> = {}
        for (const [id, product] of pairs) {
          if (product) next[id] = product
        }
        setProducts(next)
      })
      .catch(() => {
        if (live) setProducts({})
      })
    return () => {
      live = false
    }
  }, [ids])

  const spent = bag.queuedTotal + bag.purchasedTotal
  const left = bag.limit - spent

  return (
    <section className="bag-page">
      <header className="section-head bag-head">
        <p className="kicker">The bag</p>
        <h1>What you are holding.</h1>
        <p className="deck">
          {bag.count === 0
            ? 'Nothing is queued. The rack is still open.'
            : `${bag.count} queued · ${money(bag.queuedTotal)}`}
        </p>
        {shopper ? (
          <p className="deck">
            Limit {money(bag.limit)}. Purchased {money(bag.purchasedTotal)}. In the bag{' '}
            {money(bag.queuedTotal)}.{' '}
            {left < 0 ? `That is ${money(Math.abs(left))} over the limit.` : `${money(left)} left.`}
          </p>
        ) : (
          <p className="deck">
            <Link to="/login">Sign in</Link> to set a spending limit. Guests can still queue pieces.
          </p>
        )}
        {shopper && (
          <div className="loyalty-toast">
            <SwagRating
              score={loyaltyScore(bag.purchased.reduce((sum, line) => sum + line.quantity, 0))}
              label="Loyalty"
            />
            <p>Each piece you count as purchased fills one glass, up to five.</p>
          </div>
        )}
        {shopper && bag.lines.length > 0 && (
          <button className="btn btn-brass" type="button" onClick={() => bag.purchaseBag()}>
            Count the bag as purchased
          </button>
        )}
      </header>
      {bag.lines.length === 0 && (
        <p className="status">
          <Link to="/products">Shop the rack</Link>
        </p>
      )}
      {bag.lines.map((line) => {
        const product = products[line.productId]
        if (!product) {
          return (
            <article className="stage" key={`${line.productId}-${line.size}`}>
              <div className="stage-copy">
                <h1>{line.name}</h1>
                <p className="status">Pulling this piece…</p>
              </div>
            </article>
          )
        }
        return (
          <PieceStage
            key={`${line.productId}-${line.size}`}
            product={product}
            backTo="/products"
            backLabel="All products"
            kicker={`In the bag · ${line.size}`}
          >
            <LineActions
              line={line}
              onQuantity={(quantity) => bag.setQuantity(line.productId, line.size, quantity)}
              onRemove={() => bag.remove(line.productId, line.size)}
              removeLabel="Remove"
            />
          </PieceStage>
        )
      })}
      {bag.purchased.length > 0 && (
        <header className="section-head bag-head">
          <p className="kicker">Already counted</p>
          <h2>Purchased.</h2>
        </header>
      )}
      {bag.purchased.map((line) => {
        const product = products[line.productId]
        if (!product) return null
        return (
          <PieceStage
            key={`bought-${line.productId}-${line.size}`}
            product={product}
            backTo={`/products/${line.productId}`}
            backLabel="Open the piece"
            kicker={`Purchased · ${line.size}`}
          >
            <LineActions
              line={line}
              onRemove={() => bag.removePurchased(line.productId, line.size)}
              removeLabel="Take off the limit"
            />
          </PieceStage>
        )
      })}
    </section>
  )
}
