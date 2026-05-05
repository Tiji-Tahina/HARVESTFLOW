const API_BASE = '/api/v1'

export async function fetchListings() {
  const res = await fetch(`${API_BASE}/listings?skip=0&limit=100`)
  if (!res.ok) throw new Error('Failed to fetch listings')
  return res.json()
}

export async function fetchListing(id) {
  const res = await fetch(`${API_BASE}/listings/${id}`)
  if (!res.ok) throw new Error('Failed to fetch listing')
  return res.json()
}

export async function createOrder(orderData) {
  const res = await fetch(`${API_BASE}/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
  })
  if (!res.ok) throw new Error('Failed to place order')
  return res.json()
}
