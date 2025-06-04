/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary-pink': '#FF69B4',
        'soft-pink': '#FFB6C1',
        'accent-pink': '#FF1493',
        'background-blush': '#FFF0F5',
        'text-gray': '#4A4A4A',
      },
    },
  },
  plugins: [],
}
