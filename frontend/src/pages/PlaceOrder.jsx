import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchListing, createOrder } from '../services/api'

export default function PlaceOrder() {
  const { listingId } = useParams()
  const navigate = useNavigate()
  const [listing, setListing] = useState(null)
  const [quantity, setQuantity] = useState('')
  const [buyerId, setBuyerId] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetchListing(listingId).then(setListing)
  }, [listingId])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!quantity || !buyerId) {
      setError('Please fill in all fields')
      return
    }
    setSubmitting(true)
    try {
      await createOrder({
        listing_id: listingId,
        buyer_id: buyerId,
        quantity: parseFloat(quantity)
      })
      navigate('/', { state: { message: 'Order placed successfully!' } })
    } catch (err) {
      setError('Failed to place order: ' + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (!listing) return <div className="loading">Loading...</div>

  return (
    <div className="place-order">
      <h2>Place Order</h2>
      <div className="order-details">
        <h3>{listing.product?.name}</h3>
        <p>Price: ${listing.price_per_unit}/unit</p>
        <p>Available: {listing.quantity} {listing.product?.unit}</p>
        <p>Farmer: {listing.farmer?.name}</p>
      </div>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Buyer ID</label>
          <input
            type="text"
            value={buyerId}
            onChange={e => setBuyerId(e.target.value)}
            placeholder="Enter your buyer ID"
            required
          />
        </div>
        <div className="form-group">
          <label>Quantity</label>
          <input
            type="number"
            value={quantity}
            onChange={e => setQuantity(e.target.value)}
            max={listing.quantity}
            min="0.01"
            step="0.01"
            required
          />
        </div>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting} className="btn-primary">
          {submitting ? 'Placing Order...' : 'Confirm Order'}
        </button>
      </form>
    </div>
  )
}
