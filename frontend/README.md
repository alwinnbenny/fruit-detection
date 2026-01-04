Front-end React app (Vite)

Quick start:

1. From this folder run:

```bash
npm install
npm run dev
```

2. The dev server runs on `http://localhost:3000` and proxies `POST /detect_image` and `GET /live_feed` to `http://localhost:5000` by default — adjust `vite.config.js` if your Flask server uses a different port.

Notes:
- The app expects the Flask backend routes to accept the same endpoints used by the original templates (`/detect_image`, `/live_feed`).
- Build with `npm run build` and configure Flask to serve `dist/` if you want a production integration.
