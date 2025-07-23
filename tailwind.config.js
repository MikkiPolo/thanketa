/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        iosBackground: "#f2f2f7",
        iosCard: "#ffffff",
        iosAccent: "#007aff",
        iosText: "#1c1c1e",
        iosMuted: "#8e8e93",
      },
      borderRadius: {
        ios: "20px"
      },
    },
  },
  plugins: [],
}
