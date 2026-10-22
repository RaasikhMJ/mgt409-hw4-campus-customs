export type StylistRole = 'shopper' | 'stylist'

export type StylistTurn = {
  role: StylistRole
  content: string
}

export type StylistRequest = {
  message: string
  history: StylistTurn[]
  page?: {
    path: string
    productId: string
  }
}

export type StylistMatch = {
  productId: string
  name: string
  price: number
  image: string
  blurb: string
}

export type StylistReply = {
  reply: string
  products: StylistMatch[]
}

/** Same path the agent answers. products is the card contract. */
export const STYLIST_ENDPOINT = '/api/stylist'

export async function askStylist(request: StylistRequest): Promise<StylistReply> {
  const response = await fetch(STYLIST_ENDPOINT, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    throw new Error('The stylist counter did not answer.')
  }
  const payload = (await response.json()) as {
    reply?: string
    products?: StylistMatch[]
  }
  if (!payload.reply) {
    throw new Error('The stylist counter sent an empty note.')
  }
  const products = Array.isArray(payload.products) ? payload.products : []
  return { reply: payload.reply, products }
}
