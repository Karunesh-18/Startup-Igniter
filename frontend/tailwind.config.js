/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        void: '#05060f',
        charcoal: '#0a0c1a',
        midnight: '#0c1226',
        graphite: '#131829',
        // Each brand color is a DEFAULT + a light scale, not a flat string.
        // A flat string here shadows Tailwind's own default 11-step scale
        // for that name (e.g. `violet`), silently breaking any `bg-violet-400`
        // / `text-violet-400` class into a no-op. Nothing in this codebase
        // used a shaded suffix at the time of this fix, so it was a latent
        // trap rather than an active bug — this closes it while every
        // existing unshaded usage (`bg-violet`, `text-electric`, …) keeps
        // resolving via `DEFAULT`, unchanged.
        electric: { DEFAULT: '#2d7ff9', 300: '#7fb3fc', 400: '#5a9cfa', 500: '#2d7ff9', 600: '#1a6ae0', 700: '#1554b3' },
        violet: { DEFAULT: '#8b5cf6', 300: '#c4b1fb', 400: '#a688f8', 500: '#8b5cf6', 600: '#7440e8', 700: '#5c2fc2' },
        indigo: { DEFAULT: '#6366f1', 300: '#a5a6f7', 400: '#8385f4', 500: '#6366f1', 600: '#4547d6', 700: '#3638ab' },
        teal: { DEFAULT: '#14b8a6', 300: '#7fe0d4', 400: '#4bcdba', 500: '#14b8a6', 600: '#109485', 700: '#0d7669' },
        emerald: { DEFAULT: '#10b981', 300: '#7fe0bf', 400: '#4bcda1', 500: '#10b981', 600: '#0d9668', 700: '#0a7853' },
        orange: { DEFAULT: '#fb923c', 300: '#fdc394', 400: '#fca86a', 500: '#fb923c', 600: '#f3730f', 700: '#c25a0a' },
        pink: { DEFAULT: '#ec4899', 300: '#f6a8ce', 400: '#f176b3', 500: '#ec4899', 600: '#d92880', 700: '#ae1e67' },
      },
      fontFamily: {
        sans: ['Space Grotesk', 'system-ui', 'sans-serif'],
        serif: ['Instrument Serif', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        float: 'float 6s ease-in-out infinite',
        'float-slow': 'float-slow 9s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 3s ease-in-out infinite',
        'spin-slow': 'spin-slow 24s linear infinite',
      },
    },
  },
  plugins: [],
};
