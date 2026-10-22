import type { Product } from './types'

export async function loadProducts(): Promise<Product[]> {
  const response = await fetch('/api/products')
  if (!response.ok) throw new Error('The rack did not answer.')
  return response.json() as Promise<Product[]>
}

export async function loadProduct(productId: string): Promise<Product | null> {
  const response = await fetch(`/api/products/${encodeURIComponent(productId)}`)
  if (response.status === 404) return null
  if (!response.ok) throw new Error('That piece did not answer.')
  return response.json() as Promise<Product>
}
