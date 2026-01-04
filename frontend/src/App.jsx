import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Home from './components/Home'
import LiveFeed from './components/LiveFeed'
import Result from './components/Result'

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <Link to="/" className="brand">Freshness Detection</Link>
        <nav>
          <Link to="/">Home</Link>
          <Link to="/live">Live Feed</Link>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/live" element={<LiveFeed />} />
          <Route path="/result" element={<Result />} />
        </Routes>
      </main>
    </div>
  )
}
