import { money } from '../data/types'
import { useAuth } from '../auth/session'
import { useBag } from '../cart/bag'
import { loyaltyScore, SwagRating } from './SwagRating'

export function BudgetBar() {
  const { shopper } = useAuth()
  const bag = useBag()
  if (!shopper) return null

  const spent = bag.queuedTotal + bag.purchasedTotal
  const left = bag.limit - spent
  const over = left < 0
  const toasts = loyaltyScore(bag.purchased.reduce((sum, line) => sum + line.quantity, 0))

  return (
    <section className={over ? 'budget is-over' : 'budget'} aria-label="Spending limit">
      <div className="budget-read">
        <p>Spending limit</p>
        <strong>{money(bag.limit)}</strong>
      </div>
      <label className="budget-slider">
        <span className="sr-only">Set a spending limit from $25 to $2500</span>
        <input
          type="range"
          min={25}
          max={2500}
          step={25}
          value={bag.limit}
          onChange={(event) => bag.setLimit(Number(event.target.value))}
        />
      </label>
      <div className="budget-side">
        <p className="budget-tally">
          In the bag {money(bag.queuedTotal)}
          <span>Purchased {money(bag.purchasedTotal)}</span>
          <span className={over ? 'is-over' : ''}>
            {over ? `Over by ${money(Math.abs(left))}` : `${money(left)} left`}
          </span>
        </p>
        <SwagRating score={toasts} label="Loyalty" />
        <p className="budget-toast">
          {toasts === 0 ? 'Purchases pour the next glass.' : `${toasts} on the book.`}
        </p>
      </div>
    </section>
  )
}
