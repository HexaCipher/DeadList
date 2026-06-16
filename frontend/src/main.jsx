import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import App from './App.jsx';
import './index.css';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#21262D',
            color: '#E6EDF3',
            border: '1px solid #30363D',
            borderRadius: '8px',
            fontSize: '13px',
            fontFamily: 'Inter, sans-serif',
          },
          success: {
            iconTheme: { primary: '#3FB950', secondary: '#0A0E13' },
          },
          error: {
            iconTheme: { primary: '#F85149', secondary: '#0A0E13' },
          },
        }}
      />
    </BrowserRouter>
  </StrictMode>
);
