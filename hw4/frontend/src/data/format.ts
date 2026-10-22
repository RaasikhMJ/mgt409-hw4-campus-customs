import { laneOf, type Product } from './types'

const SWAG_HITS = [
  'graphic',
  'crest',
  'vintage',
  'logo',
  'script',
  'arched',
  'helmet',
  'embroider',
  'champion',
  'striped',
  'varsity',
  'game',
]

export function swagRating(product: Product): number {
  const text = `${product.name} ${product.description}`.toLowerCase()
  let points = 0
  for (const word of SWAG_HITS) {
    if (text.includes(word)) points += 1
  }
  if (product.colors.length >= 4) points += 1
  const lane = laneOf(product.garmentType)
  if (lane === 'Hoodies' || lane === 'Jackets' || lane === 'Quarter-zips') {
    points += 1
  }
  if (points <= 0) return 2
  if (points === 1) return 3
  if (points === 2) return 4
  return 5
}

export function shortDescription(description: string, max = 118): string {
  const sentence = description.split(/(?<=\.)\s/)[0] ?? description
  if (sentence.length <= max) return sentence
  const cut = sentence.slice(0, max)
  const lastSpace = cut.lastIndexOf(' ')
  const end = lastSpace > 48 ? lastSpace : max
  return `${cut.slice(0, end).trim()}…`
}
