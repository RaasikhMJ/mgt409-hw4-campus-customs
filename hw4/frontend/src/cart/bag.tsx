import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { useAuth } from '../auth/session'

export type BagLine = {
  productId: string
  name: string
  price: number
  image: string
  size: string
  quantity: number
}

export type BoughtLine = BagLine

type BudgetFile = {
  limit: number
  purchased: BoughtLine[]
}

type BagValue = {
  lines: BagLine[]
  count: number
  queuedTotal: number
  add: (line: Omit<BagLine, 'quantity'> & { quantity?: number }) => void
  setQuantity: (productId: string, size: string, quantity: number) => void
  remove: (productId: string, size: string) => void
  limit: number
  setLimit: (value: number) => void
  purchased: BoughtLine[]
  purchasedTotal: number
  purchaseBag: () => void
  removePurchased: (productId: string, size: string) => void
}

const BAG_KEY = 'cc-bag'
const DEFAULT_LIMIT = 400

const BagContext = createContext<BagValue | null>(null)

function clampLimit(value: number): number {
  if (!Number.isFinite(value)) return DEFAULT_LIMIT
  const stepped = Math.round(value / 25) * 25
  return Math.min(2500, Math.max(25, stepped))
}

function cleanLine(value: unknown): BagLine | null {
  if (!value || typeof value !== 'object') return null
  const row = value as Partial<BagLine>
  if (typeof row.productId !== 'string' || typeof row.size !== 'string') return null
  const quantity = Number(row.quantity)
  const price = Number(row.price)
  if (!Number.isFinite(quantity) || quantity < 1) return null
  if (!Number.isFinite(price) || price < 0) return null
  return {
    productId: row.productId,
    name: typeof row.name === 'string' ? row.name : row.productId,
    price,
    image: typeof row.image === 'string' ? row.image : '',
    size: row.size,
    quantity: Math.min(10, Math.floor(quantity)),
  }
}

function readLines(raw: string | null): BagLine[] {
  try {
    const parsed = JSON.parse(raw || '[]') as unknown
    if (!Array.isArray(parsed)) return []
    return parsed.map(cleanLine).filter((line): line is BagLine => line !== null)
  } catch {
    return []
  }
}

function budgetKey(userId: number): string {
  return `cc-budget:${userId}`
}

function readBudget(userId: number): BudgetFile {
  try {
    const parsed = JSON.parse(localStorage.getItem(budgetKey(userId)) || '') as Partial<BudgetFile>
    const purchased = Array.isArray(parsed.purchased)
      ? parsed.purchased.map(cleanLine).filter((line): line is BagLine => line !== null)
      : []
    return { limit: clampLimit(Number(parsed.limit)), purchased }
  } catch {
    return { limit: DEFAULT_LIMIT, purchased: [] }
  }
}

function samePiece(line: BagLine, productId: string, size: string): boolean {
  return line.productId === productId && line.size === size
}

function total(lines: BagLine[]): number {
  return lines.reduce((sum, line) => sum + line.price * line.quantity, 0)
}

export function BagProvider({ children }: { children: ReactNode }) {
  const { shopper } = useAuth()
  const [lines, setLines] = useState<BagLine[]>(() => readLines(localStorage.getItem(BAG_KEY)))
  const [limit, setLimitState] = useState(DEFAULT_LIMIT)
  const [purchased, setPurchased] = useState<BoughtLine[]>([])
  const [budgetReady, setBudgetReady] = useState(false)

  useEffect(() => {
    localStorage.setItem(BAG_KEY, JSON.stringify(lines))
  }, [lines])

  useEffect(() => {
    setBudgetReady(false)
    if (!shopper) {
      setPurchased([])
      return
    }
    const saved = readBudget(shopper.id)
    setLimitState(saved.limit)
    setPurchased(saved.purchased)
    setBudgetReady(true)
  }, [shopper?.id])

  useEffect(() => {
    if (!shopper || !budgetReady) return
    const file: BudgetFile = { limit, purchased }
    localStorage.setItem(budgetKey(shopper.id), JSON.stringify(file))
  }, [shopper, budgetReady, limit, purchased])

  const value = useMemo<BagValue>(() => {
    return {
      lines,
      count: lines.reduce((sum, line) => sum + line.quantity, 0),
      queuedTotal: total(lines),
      add(incoming) {
        setLines((current) => {
          const quantity = incoming.quantity ?? 1
          const found = current.find((line) => samePiece(line, incoming.productId, incoming.size))
          if (!found) {
            return [...current, { ...incoming, quantity: Math.min(10, quantity) }]
          }
          return current.map((line) =>
            samePiece(line, incoming.productId, incoming.size)
              ? { ...line, quantity: Math.min(10, line.quantity + quantity) }
              : line,
          )
        })
      },
      setQuantity(productId, size, quantity) {
        setLines((current) =>
          current
            .map((line) =>
              samePiece(line, productId, size)
                ? { ...line, quantity: Math.min(10, Math.max(0, Math.floor(quantity))) }
                : line,
            )
            .filter((line) => line.quantity > 0),
        )
      },
      remove(productId, size) {
        setLines((current) => current.filter((line) => !samePiece(line, productId, size)))
      },
      limit,
      setLimit(next) {
        if (!shopper) return
        setLimitState(clampLimit(next))
      },
      purchased,
      purchasedTotal: total(purchased),
      purchaseBag() {
        if (!shopper || lines.length === 0) return
        setPurchased((current) => [...current, ...lines])
        setLines([])
      },
      removePurchased(productId, size) {
        setPurchased((current) => current.filter((line) => !samePiece(line, productId, size)))
      },
    }
  }, [lines, limit, purchased, shopper])

  return <BagContext.Provider value={value}>{children}</BagContext.Provider>
}

export function useBag(): BagValue {
  const value = useContext(BagContext)
  if (!value) throw new Error('useBag must be used inside BagProvider')
  return value
}
