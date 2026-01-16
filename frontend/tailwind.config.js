/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0c4a6e',
          light: '#0369a1',
          dark: '#082f49',
        },
        secondary: {
          DEFAULT: '#0369a1',
          light: '#0ea5e9',
          dark: '#075985',
        },
        accent: '#f59e0b',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        // Cores dos módulos para gráficos
        module1: '#3b82f6', // Azul
        module2: '#10b981', // Verde
        module3: '#f59e0b', // Laranja
        module4: '#8b5cf6', // Roxo
        module5: '#ec4899', // Pink
        module6: '#14b8a6', // Teal
        module7: '#6366f1', // Índigo
      },
    },
  },
  plugins: [],
}
