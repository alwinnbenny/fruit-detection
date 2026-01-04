import React from 'react'
import { useLocation, Link } from 'react-router-dom'

function getQueryParams() {
  const params = new URLSearchParams(window.location.search)
  return {
    result_image: params.get('result_image'),
    unique_id: params.get('unique_id')
  }
}

export default function Result() {
  const { state } = useLocation()
  const data = state?.data || {}

  // build image src: prefer backend-provided image_url, then result_image + unique_id from state, then query params
  const q = getQueryParams()
  let imgSrc = data.image_url || (data.result_image ? `/static/uploads/${data.result_image}${data.unique_id ? '?' + data.unique_id : ''}` : (q.result_image ? `/static/uploads/${q.result_image}${q.unique_id ? '?' + q.unique_id : ''}` : null))
  // If the src is relative (starts with /static) and we're on the dev server, point to Flask backend
  if (imgSrc && imgSrc.startsWith('/static')) {
    imgSrc = (process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000') + imgSrc
  }

  return (
    <div className="card">
      <h1>Detection Result</h1>

      {data.error && <p className="error">{data.error}</p>}

      {imgSrc ? (
        <>
          <div className="result-media">
            <img src={imgSrc} alt="detection result" className="result-img" />
          </div>

          <div className="result-actions">
            <a className="btn" href={imgSrc} target="_blank" rel="noreferrer">Open Image</a>
            <a className="btn primary" href={imgSrc} download>Download</a>
            <Link to="/" className="btn">Back</Link>
          </div>
        </>
      ) : (
        <div>
          <p className="muted">No result image available.</p>
          <div style={{ marginTop: 12 }}>
            <Link to="/" className="btn">Back</Link>
          </div>
        </div>
      )}
    </div>
  )
}
