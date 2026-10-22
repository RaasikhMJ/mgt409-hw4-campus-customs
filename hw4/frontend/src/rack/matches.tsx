import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import type { StylistMatch } from '../chat/stylist'

type Pull = {
  query: string
  products: StylistMatch[]
  searching: boolean
}

type MatchContextValue = Pull & {
  show: (query: string, products: StylistMatch[]) => void
  setSearching: (searching: boolean) => void
  clear: () => void
}

const MatchContext = createContext<MatchContextValue | null>(null)

export function MatchProvider({ children }: { children: ReactNode }) {
  const [pull, setPull] = useState<Pull>({ query: '', products: [], searching: false })
  const value = useMemo<MatchContextValue>(
    () => ({
      ...pull,
      show: (query, products) => setPull({ query, products, searching: false }),
      setSearching: (searching) => setPull((current) => ({ ...current, searching })),
      clear: () => setPull({ query: '', products: [], searching: false }),
    }),
    [pull],
  )
  return <MatchContext.Provider value={value}>{children}</MatchContext.Provider>
}

export function useMatches(): MatchContextValue {
  const value = useContext(MatchContext)
  if (!value) throw new Error('Match rack is outside its provider.')
  return value
}
