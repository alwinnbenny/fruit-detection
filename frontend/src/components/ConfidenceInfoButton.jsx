import React, { useState, useEffect, useCallback } from 'react'

export default function ConfidenceInfoButton() {
  const [open, setOpen] = useState(false)

  const close = useCallback(() => setOpen(false), [])

  // Close on Escape key
  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') close() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, close])

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  return (
    <>
      {/* Floating info button */}
      <button
        className="info-fab"
        onClick={() => setOpen(true)}
        title="What is a confidence score?"
        aria-label="More info about confidence scores"
        id="confidence-info-btn"
      >
        <span className="info-fab-icon">i</span>
      </button>

      {/* Modal popup */}
      {open && (
        <div className="info-modal-backdrop" onClick={close}>
          <div className="info-modal" onClick={(e) => e.stopPropagation()}>
            <button className="info-modal-close" onClick={close} aria-label="Close">&times;</button>

            <div className="info-modal-header">
              <span className="info-modal-emoji">📊</span>
              <h2>Understanding Confidence Scores</h2>
            </div>

            <div className="info-modal-body">
              <p>
                A <strong>confidence score</strong> tells you how sure the AI model is about its
                prediction. It's shown as a percentage next to each detected item.
              </p>
              <p>
                For example, if the model says <em>"Fresh Apple: 92%"</em>, it means the AI is
                92% confident that the item is a fresh apple.
              </p>

              <h3>What do the scores mean?</h3>

              <div className="confidence-levels">
                <div className="confidence-level high">
                  <span className="confidence-bar" />
                  <div className="confidence-info">
                    <strong>90% – 100%</strong>
                    <span>Very High Confidence</span>
                  </div>
                  <p>The model is almost certain about its prediction. You can strongly trust this result.</p>
                </div>

                <div className="confidence-level medium">
                  <span className="confidence-bar" />
                  <div className="confidence-info">
                    <strong>70% – 89%</strong>
                    <span>High Confidence</span>
                  </div>
                  <p>A reliable prediction. The model is fairly sure, though there's a small chance of error.</p>
                </div>

                <div className="confidence-level low">
                  <span className="confidence-bar" />
                  <div className="confidence-info">
                    <strong>45% – 69%</strong>
                    <span>Moderate Confidence</span>
                  </div>
                  <p>The model's best guess, but less certain. This can happen with blurry images or unusual angles.</p>
                </div>
              </div>

              <div className="confidence-tip">
                <span>💡</span>
                <p>
                  <strong>Tip:</strong> For the most accurate results, use well-lit, clear photos
                  with the fruit or vegetable clearly visible. Predictions below 45% confidence
                  are automatically filtered out.
                </p>
              </div>
            </div>

            <button className="btn btn-primary info-modal-got-it" onClick={close}>
              Got it!
            </button>
          </div>
        </div>
      )}
    </>
  )
}
