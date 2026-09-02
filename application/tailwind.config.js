/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./frontend/**/*.html", "./frontend/**/*.js"],
  safelist: [
    { pattern: /(bg|border|text)-(rose|amber|emerald|stone)-(50|100|200|500|600|700|800|900)/ },
    { pattern: /from-(rose|amber|emerald|stone)-(500|700)/ },
    { pattern: /to-(rose|amber|emerald|stone)-(500|700)/ },
  ],
  theme: {
    extend: {
      colors: {
        brand: { 50: "#f0fdf4", 100: "#dcfce7", 500: "#0c4a3e", 600: "#0a3d33", 700: "#083029" },
        accent: { 500: "#d97706", 600: "#b45309" },
      },
      fontFamily: {
        sans: ["-apple-system", "BlinkMacSystemFont", "SF Pro Text", "PingFang SC", "Microsoft YaHei", "sans-serif"],
        serif: ["Source Han Serif SC", "Songti SC", "SimSun", "serif"],
      },
    },
  },
  plugins: [],
};
