import { Routes, Route, Link } from 'react-router-dom'
import Listings from './pages/Listings'
import PlaceOrder from './pages/PlaceOrder'

export default function App() {
  return (
    <div className="app">
      <nav className="navbar">
        <h1>HarvestFlow Buyer Dashboard</h1>
        <div className="nav-links">
          <Link to="/">Available Listings</Link>
        </div>
      </nav>
      <main className="container">
        <Routes>
          <Route path="/" element={<Listings />} />
          <Route path="/order/:listingId" element={<PlaceOrder />} />
        </Routes>
      </main>
    </div>
  )
}
