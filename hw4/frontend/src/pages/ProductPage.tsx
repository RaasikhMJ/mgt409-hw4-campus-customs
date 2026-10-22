import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useBag } from '../cart/bag'
import { PieceStage } from '../components/PieceStage'
import { loadProduct } from '../data/shop'
import type { Product } from '../data/types'

export function ProductPage() {
  const { productId } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [status, setStatus] = useState<'loading' | 'ready' | 'missing' | 'error'>('loading')
  const [size, setSize] = useState('')
  const [queued, setQueued] = useState(false)
  const bag = useBag()

  useEffect(() => {
    if (!productId) return
    let live = true
    setStatus('loading')
    loadProduct(productId)
      .then((item) => {
        if (!live) return
        setProduct(item)
        setStatus(item ? 'ready' : 'missing')
      })
      .catch(() => {
        if (live) setStatus('error')
      })
    return () => {
      live = false
    }
  }, [productId])

  useEffect(() => {
    document.title = product
      ? `${product.name} · Campus Customs`
      : 'Campus Customs'
  }, [product])

  useEffect(() => {
    if (status !== 'ready' || !product) return
    const open = product.sizes.find((item) => item.quantity > 0)
    setSize(open?.size ?? '')
    setQueued(false)
    document.querySelector('.stage')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [status, productId, product])

  if (status === 'loading') {
    return (
      <section className="page narrow">
        <p className="status">Pulling this piece…</p>
      </section>
    )
  }

  if (status === 'error') {
    return (
      <section className="page narrow">
        <h1>The counter did not answer.</h1>
        <Link className="btn btn-brass" to="/products">
          Back to products
        </Link>
      </section>
    )
  }

  if (!product || status === 'missing') {
    return (
      <section className="page narrow">
        <h1>That piece is not on the rack.</h1>
        <Link className="btn btn-brass" to="/products">
          Back to products
        </Link>
      </section>
    )
  }

  return (
    <PieceStage product={product}>
      <div className="bag-add">
        <p className="eyebrow">Queue a size</p>
        <div className="filters" role="group" aria-label="Size to queue">
          {product.sizes.map((item) => (
            <button
              key={item.size}
              type="button"
              className={item.size === size ? 'is-on' : ''}
              aria-pressed={item.size === size}
              disabled={item.quantity === 0}
              onClick={() => {
                setSize(item.size)
                setQueued(false)
              }}
            >
              {item.size}
            </button>
          ))}
        </div>
        <button
          className="btn btn-brass"
          type="button"
          disabled={size === ''}
          onClick={() => {
            bag.add({
              productId: product.productId,
              name: product.name,
              price: product.price,
              image: product.image,
              size,
            })
            setQueued(true)
          }}
        >
          Add to the bag
        </button>
        {queued && (
          <p className="status">
            In the bag. <Link to="/cart">Open it</Link>
          </p>
        )}
      </div>
    </PieceStage>
  )
}
