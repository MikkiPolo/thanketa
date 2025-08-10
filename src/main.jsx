import './index.css'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './test-config.js'
import telegramWebApp from './telegramWebApp.js'
//import 'bootstrap/dist/css/bootstrap.min.css'

// Initialize Telegram WebApp and viewport helpers ASAP
try { telegramWebApp.init(); } catch (e) {}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
