/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'qadsiah-red': '#B22222',
        'header-grey': '#1F2937'
      }
    },
  },
  plugins: [],
}

