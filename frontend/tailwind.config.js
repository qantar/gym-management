/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          0: '#0a0b0e',
          1: '#0f1117',
          2: '#14161f',
          3: '#1a1d2a',
          4: '#1f2235',
        },
        accent: {
          DEFAULT: '#6c63ff',
          2: '#4fc3f7',
          3: '#00e5a0',
          4: '#ff6b6b',
          5: '#ffc107',
        },
        text: {
          0: '#f0f2ff',
          1: '#9ba3c0',
          2: '#636882',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
