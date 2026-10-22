export type SizeStock = {
  size: string
  quantity: number
}

export type Product = {
  productId: string
  name: string
  garmentType: string
  description: string
  price: number
  image: string
  colors: string[]
  sizes: SizeStock[]
}

export const LANES = [
  'All',
  'Hoodies',
  'Crews',
  'Tees',
  'Quarter-zips',
  'Jackets',
] as const

export type Lane = (typeof LANES)[number]

export function laneOf(garmentType: string): Exclude<Lane, 'All'> {
  const kind = garmentType.toLowerCase()
  if (kind.includes('quarter')) return 'Quarter-zips'
  if (kind.includes('jacket') || kind.includes('bomber')) return 'Jackets'
  if (kind.includes('hood')) return 'Hoodies'
  if (kind.includes('crew') || kind.includes('mockneck')) return 'Crews'
  return 'Tees'
}

export function money(price: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(price)
}
