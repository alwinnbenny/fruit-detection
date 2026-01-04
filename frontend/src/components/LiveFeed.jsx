import React, { useRef, useState, useEffect } from 'react'

export default function LiveFeed() {
  const imgRef = useRef(null)
  const canvasRef = useRef(null)
  const [streaming, setStreaming] = useState(true)
  const [loading, setLoading] = useState(true)
  const [connected, setConnected] = useState(false)

  function toggleStream() {
    setStreaming(s => !s)
    if (streaming) {
      // stop stream by removing src
      if (imgRef.current) imgRef.current.src = ''
      setConnected(false)
      setLoading(false)
    } else {
      if (imgRef.current) imgRef.current.src = '/video_feed'
      setLoading(true)
    }
  }

  useEffect(() => {
    // start stream on mount
    if (imgRef.current && streaming) imgRef.current.src = '/video_feed'
    return () => {
      if (imgRef.current) imgRef.current.src = ''
    }
  }, [])

  function captureSnapshot() {
    const img = imgRef.current
    const canvas = canvasRef.current
    if (!img || !canvas) return

    const w = img.naturalWidth || img.width
    const h = img.naturalHeight || img.height
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    try {
      ctx.drawImage(img, 0, 0, w, h)
      const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
      // open snapshot in new tab
      const win = window.open()
      if (win) win.document.body.innerHTML = `<img src="${dataUrl}" style="max-width:100%">`
    } catch (err) {
      console.error('Capture failed', err)
    }
  }

  return (
    <div className="card">
      <div className="live-header">
        <div>
          <h1>Live Feed</h1>
          <p className="muted">Live camera feed with snapshot controls. The feed is proxied to your Flask backend.</p>
        </div>
        <div className="status">
          <span className={"status-pill " + (connected ? 'ok pulse' : 'bad')}>{connected ? 'Connected' : (loading ? 'Connecting…' : 'Disconnected')}</span>
        </div>
      </div>

      <div className="live-wrap grid">
        <div className="feed">
          {loading && <div className="feed-overlay"><div className="spinner" /></div>}
          <img
            ref={imgRef}
            src={streaming ? '/video_feed' : ''}
            alt="live feed"
            className="mjpeg"
            onError={() => { setLoading(false); setConnected(false) }}
            onLoad={() => { setLoading(false); setConnected(true) }}
          />
        </div>

        <aside className="sidebar">
          <div className="controls">
            <button className="btn" onClick={toggleStream} title={streaming ? 'Stop Stream' : 'Start Stream'}>
              {streaming ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/></svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5 3v18l15-9L5 3z" fill="currentColor"/></svg>
              )}
              <span className="btn-label">{streaming ? 'Stop' : 'Start'}</span>
            </button>

            <button className="btn primary" onClick={captureSnapshot} title="Capture Snapshot">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 7a5 5 0 100 10 5 5 0 000-10zm7-2h-2.2l-1.4-2H8.6L7.2 5H5a2 2 0 00-2 2v10a2 2 0 002 2h14a2 2 0 002-2V7a2 2 0 00-2-2z" fill="currentColor"/></svg>
              <span className="btn-label">Capture</span>
            </button>
          </div>

          <div className="panel">
            <h3>Session</h3>
            <p className="muted">Use the controls to manage the live detection feed. Snapshots open in a new tab.</p>
          </div>
        </aside>

        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>
    </div>
  )
}
