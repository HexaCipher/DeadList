/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-base':       '#0A0E13',
        'bg-surface':    '#161B22',
        'bg-elevated':   '#21262D',
        'border-subtle': '#30363D',
        'text-primary':  '#E6EDF3',
        'text-secondary':'#8B949E',
        'text-disabled': '#484F58',
        'accent-green':  '#3FB950',
        'accent-amber':  '#D29922',
        'accent-red':    '#F85149',
        'accent-blue':   '#58A6FF',
        'brand':         '#1F6FEB',
        'glow-red':      'rgba(248, 81, 73, 0.15)',
        'glow-green':    'rgba(63, 185, 80, 0.10)',
        'hidden-bg':     '#3D0B09',
        'suspicious-bg': '#2D1C00',
        'anomalous-bg':  '#0D1F38',
        'clean-bg':      '#0D1F14',
      },
      fontFamily: {
        sans:  ['Inter', 'system-ui', 'sans-serif'],
        mono:  ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      borderRadius: {
        'card':  '8px',
        'badge': '4px',
        'btn':   '6px',
      },
      boxShadow: {
        'glow-red':   '0 0 20px rgba(248, 81, 73, 0.2)',
        'glow-green': '0 0 20px rgba(63, 185, 80, 0.15)',
        'glow-amber': '0 0 20px rgba(210, 153, 34, 0.15)',
        'glow-blue':  '0 0 20px rgba(88, 166, 255, 0.15)',
        'glow-brand': '0 0 20px rgba(31, 111, 235, 0.25)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan':       'scan 2s ease-in-out infinite',
        'fade-in':    'fadeIn 0.3s ease-out',
        'slide-in':   'slideIn 0.3s ease-out',
        'slide-out':  'slideOut 0.2s ease-in',
        'count-up':   'countUp 1s ease-out',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        scan: {
          '0%, 100%': { opacity: '0.3' },
          '50%':      { opacity: '1' },
        },
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%':   { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        slideOut: {
          '0%':   { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(100%)' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 5px rgba(248, 81, 73, 0.3)' },
          '50%':      { boxShadow: '0 0 25px rgba(248, 81, 73, 0.6)' },
        },
      },
    },
  },
  plugins: [],
}
