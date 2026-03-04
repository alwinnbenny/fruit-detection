import React, { useState, useMemo } from 'react'
import UploadPanel from './components/UploadPanel'
import CameraPanel from './components/CameraPanel'

const TABS = [
  {
    id: 'upload',
    label: 'Upload',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
    ),
  },
  {
    id: 'camera',
    label: 'Live Camera',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
      </svg>
    ),
  },
]

const FRUITS = ['🍎', '🍌', '🍓', '🍊', '🍇', '🥝', '🍍', '🥭', '🍑', '🫐', '🍒', '🍋', '🥑', '🍉', '🫒']

export default function App() {
  const [activeTab, setActiveTab] = useState('upload')

  // Generate floating fruit positions (stable across renders)
  const floatingFruits = useMemo(() =>
    Array.from({ length: 18 }).map((_, i) => ({
      id: i,
      emoji: FRUITS[i % FRUITS.length],
      left: `${5 + (i * 37) % 90}%`,
      size: `${22 + (i * 7) % 20}px`,
      dur: `${10 + (i * 3) % 14}s`,
      delay: `${-(i * 2.3) % 12}s`,
    })), [])

  return (
    <div className="app">
      {/* Floating fruit background */}
      <div className="fruit-bg" aria-hidden="true">
        {floatingFruits.map(f => (
          <span
            key={f.id}
            className="floating-fruit"
            style={{
              left: f.left,
              fontSize: f.size,
              '--dur': f.dur,
              '--delay': f.delay,
              animationDelay: f.delay,
            }}
          >
            {f.emoji}
          </span>
        ))}
      </div>

      <header className="topbar">
        <span className="brand">
          <span className="brand-icon">🍎</span>
          Freshness Detection
        </span>

        <nav className="tab-nav">
          {TABS.map(tab => (
            <button
              key={tab.id}
              className={`tab-btn${activeTab === tab.id ? ' active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="app-main">
        {activeTab === 'upload' && <UploadPanel key="upload" />}
        {activeTab === 'camera' && <CameraPanel key="camera" />}
      </main>
    </div>
  )
}
