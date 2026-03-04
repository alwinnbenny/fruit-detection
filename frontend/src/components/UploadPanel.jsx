import React, { useState, useRef } from 'react'

export default function UploadPanel() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  function handleFile(f) {
    if (!f) return
    setFile(f)
    setResult(null)
    setError(null)
    const reader = new FileReader()
    reader.onload = e => setPreview(e.target.result)
    reader.readAsDataURL(f)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0])
  }

  async function handleDetect() {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    const fd = new FormData()
    fd.append('image', file)

    try {
      const res = await fetch('/detect_image', {
        method: 'POST',
        headers: { 'Accept': 'application/json' },
        body: fd
      })
      const data = await res.json()
      if (data.error) {
        setError(data.error)
      } else {
        setResult(data)
      }
    } catch (err) {
      setError('Detection request failed. Is the Flask server running?')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  function handleClear() {
    setFile(null)
    setPreview(null)
    setResult(null)
    setError(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  // Build result image URL
  let resultSrc = null
  if (result) {
    resultSrc = result.image_url || `/static/uploads/${result.result_image}`
  }

  return (
    <div className="panel-container">
      <div className="card">
        <div className="card-header">
          <h2>🔍 Image Detection</h2>
          <p>Upload a photo of fruits or vegetables to detect their freshness.</p>
        </div>

        {/* Upload zone */}
        <div
          className={`upload-zone${dragOver ? ' drag-over' : ''}${file ? ' has-file' : ''}`}
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            onChange={e => handleFile(e.target.files?.[0])}
          />
          <div className="upload-icon">{file ? '✅' : '📁'}</div>
          <h3>{file ? 'Image selected' : 'Drop an image here or click to browse'}</h3>
          <p>{file ? 'Click to change the image' : 'Supports JPG, PNG, WebP'}</p>
        </div>

        {/* Preview strip */}
        {file && preview && (
          <div className="preview-strip">
            <img src={preview} alt="preview" className="preview-thumb" />
            <div className="preview-info">
              <div className="preview-name">{file.name}</div>
              <div className="preview-size">{(file.size / 1024).toFixed(1)} KB</div>
            </div>
            <div className="btn-group">
              <button className="btn-primary btn" onClick={handleDetect} disabled={loading}>
                {loading ? (
                  <>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2v4m0 12v4m-7.07-3.93l2.83-2.83m8.48-8.48l2.83-2.83M2 12h4m12 0h4m-3.93 7.07l-2.83-2.83M7.76 7.76L4.93 4.93"/></svg>
                    Detecting…
                  </>
                ) : (
                  <>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                    Detect Freshness
                  </>
                )}
              </button>
              <button className="btn" onClick={handleClear}>Clear</button>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="result-area" style={{ color: 'var(--red)' }}>
            <p>⚠️ {error}</p>
          </div>
        )}

        {/* Loading overlay */}
        {loading && (
          <div className="result-area">
            <div className="result-image-wrap" style={{ minHeight: 200 }}>
              <div className="loading-overlay">
                <div className="spinner" />
                <p>Analyzing image…</p>
              </div>
            </div>
          </div>
        )}

        {/* Result */}
        {result && resultSrc && (
          <div className="result-area">
            <div className="result-image-wrap">
              <img src={resultSrc} alt="detection result" />
            </div>
            <div className="result-actions">
              <a className="btn" href={resultSrc} target="_blank" rel="noreferrer">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                Open Full Image
              </a>
              <a className="btn-primary btn" href={resultSrc} download>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Download
              </a>
              <button className="btn" onClick={handleClear}>New Detection</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
