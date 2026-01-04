import React, { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Home() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    const fd = new FormData()
    fd.append('image', file)

    try {
      const res = await fetch('/detect_image', {
        method: 'POST',
        headers: { 'Accept': 'application/json' },
        body: fd
      })
      // backend may return JSON or HTML; try JSON first
      let data
      try { data = await res.json() } catch { data = { message: await res.text() } }
      navigate('/result', { state: { data } })
    } catch (err) {
      console.error(err)
      navigate('/result', { state: { data: { error: 'Request failed' } } })
    } finally { setLoading(false) }
  }

  const FRUITS = ['🍎','🍌','🍓','🍊','🍇','🥝','🍍','🥭','🍑']

  const animatedFruits = useMemo(() => {
    return Array.from({ length: 20 }).map((_, i) => {
      const left = Math.round(Math.random() * 90)
      const top = Math.round(Math.random() * 80)
      const size = 24 + Math.round(Math.random() * 36)
      // faster durations (shorter = faster)
      const dur = (6 + Math.random() * 8).toFixed(1)
      const delay = (-Math.random() * 6).toFixed(1)
      const anim = `move${(i % 4) + 1}`
      return { id: i, ch: FRUITS[i % FRUITS.length], left, top, size, dur, delay, anim }
    })
  }, [])

  return (
    <div className="home-page">
      <div className="fruit-bg" aria-hidden>
        {animatedFruits.map(({ id, ch, left, top, size, dur, delay, anim }) => (
          <span
            key={id}
            className={`fruit ${anim}`}
            style={{ left: `${left}%`, top: `${top}%`, fontSize: `${size}px`, animationDuration: `${dur}s`, animationDelay: `${delay}s` }}
          >
            {ch}
          </span>
        ))}
      </div>

      <div className="card">
      <h1>Choose Detection Mode</h1>

      <div className="mode">
        <h2>Live Feed Detection</h2>
        <p>Start a live camera feed detection session.</p>
        <a className="btn" href="/live_feed" target="_blank" rel="noreferrer">Open Live Feed</a>
      </div>

      <div className="mode">
        <h2>Image Upload Detection</h2>
        <form onSubmit={handleSubmit} className="upload-form">
          <input type="file" accept="image/*" onChange={e => setFile(e.target.files[0])} />
          <button className="btn primary" type="submit" disabled={loading}>{loading ? 'Detecting…' : 'Detect'}</button>
        </form>
      </div>
      </div>
    </div>
  )
}
