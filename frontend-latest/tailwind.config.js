/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // 👈 enables manual dark mode with a class
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'weather-blue': '#1e3a8a',
        'weather-light': '#1e3a8a',
        'sunny': '#1e3a8a',
        'cloudy': '#1e3a8a',
        'rainy': '#1e3a8a',
        'snowy': '#1e3a8a',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'sunny-gradient': 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
        'cloudy-gradient': 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)',
        'rainy-gradient': 'linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%)',
        'night-gradient': 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'bounce-slow': 'bounce 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
