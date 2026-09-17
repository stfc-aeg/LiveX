import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

import { OdinErrorContext } from 'odin-react';

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Root element not found')
}

createRoot(rootElement).render(
  <StrictMode>
    <OdinErrorContext>
      <App />
    </OdinErrorContext>
  </StrictMode>,
)
