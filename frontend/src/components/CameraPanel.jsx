import React, { useRef, useState, useEffect } from 'react'

export default function CameraPanel() {
    const imgRef = useRef(null)
    const [streaming, setStreaming] = useState(false)
    const [loading, setLoading] = useState(false)
    const [connected, setConnected] = useState(false)
    const [error, setError] = useState(null)

    function startStream() {
        setLoading(true)
        setError(null)
        setStreaming(true)
        if (imgRef.current) {
            imgRef.current.src = '/video_feed'
        }
    }

    function stopStream() {
        if (imgRef.current) {
            imgRef.current.src = ''
        }
        setStreaming(false)
        setConnected(false)
        setLoading(false)
    }

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (imgRef.current) imgRef.current.src = ''
        }
    }, [])

    return (
        <div className="panel-container">
            <div className="card">
                <div className="card-header">
                    <h2>📹 Live Camera Detection</h2>
                    <p>Real-time freshness detection using your webcam. Detection runs every 5th frame for smooth video.</p>
                </div>

                {/* Camera feed */}
                <div className="camera-container mjpeg-container">
                    {loading && !connected && (
                        <div className="camera-overlay">
                            <div className="spinner" />
                            <p>Connecting to camera…</p>
                        </div>
                    )}

                    {!streaming && (
                        <div className="camera-overlay">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
                            </svg>
                            <p>{error || 'Click "Start Camera" to begin'}</p>
                        </div>
                    )}

                    <img
                        ref={imgRef}
                        alt="live feed"
                        className="mjpeg-img"
                        style={{ display: streaming ? 'block' : 'none' }}
                        onLoad={() => { setLoading(false); setConnected(true) }}
                        onError={() => {
                            setLoading(false)
                            setConnected(false)
                            if (streaming) setError('Camera feed lost. Try restarting.')
                        }}
                    />
                </div>

                {/* Controls */}
                <div className="camera-controls">
                    <div className="btn-group">
                        {!streaming ? (
                            <button className="btn btn-success" onClick={startStream}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="5 3 19 12 5 21 5 3" /></svg>
                                Start Camera
                            </button>
                        ) : (
                            <button className="btn btn-danger" onClick={stopStream}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="6" y="6" width="12" height="12" rx="1" /></svg>
                                Stop Camera
                            </button>
                        )}
                    </div>

                    <div style={{ display: 'flex', gap: 8 }}>
                        {streaming && connected && (
                            <span className="status-badge live">
                                <span className="status-dot" />
                                Live
                            </span>
                        )}
                        {streaming && !connected && (
                            <span className="status-badge detecting">
                                <span className="status-dot" />
                                Connecting…
                            </span>
                        )}
                        {!streaming && (
                            <span className="status-badge off">
                                <span className="status-dot" />
                                Off
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
