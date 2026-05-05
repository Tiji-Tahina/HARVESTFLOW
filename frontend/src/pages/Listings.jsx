import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchListings } from '../services/api'

export default function Listings() {
  const [listings, setListings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchListings()
      .then(setListings)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading listings...</div>

  return (
    <div className="listings">
      <h2>Available Produce</h2>
      {listings.length === 0 && <p>No listings available.</p>}
      <div className="listings-grid">
        {listings
          .filter(l => l.status === 'active')
          .map(listing => (
            <div key={listing.id} className="listing-card">
              <h3>{listing.product?.name || 'Produce'}</h3>
              <p className="price">${listing.price_per_unit}/unit</p>
              <p>Quantity: {listing.quantity} {listing.product?.unit || 'units'}</p>
              <p className="farmer">Farmer: {listing.farmer?.name || 'Unknown'}</p>
              <Link to={`/order/${listing.id}`} className="btn-primary">
                Place Order
              </Link>
            </div>
          ))}
      </div>
    </div>
  )
}
