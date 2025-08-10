import type { Config } from "tailwindcss"

const config = {
  darkMode: "class",
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
	],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        glass: {
          dark: {
            DEFAULT: 'rgba(255, 255, 255, 0.05)',
            strong: 'rgba(255, 255, 255, 0.08)',
            border: 'rgba(255, 255, 255, 0.1)',
          },
          light: {
            DEFAULT: 'rgba(255, 255, 255, 0.25)',
            strong: 'rgba(255, 255, 255, 0.35)',
            border: 'rgba(255, 255, 255, 0.3)',
          }
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
      },
      backgroundImage: {
        'gradient-dark': 'linear-gradient(135deg, #000000 0%, #0d1117 50%, #1a1a1a 100%)',
        'gradient-light': 'linear-gradient(135deg, #ffffff 0%, #f1f5f9 50%, #f8fafc 100%)',
        'glass-dark': 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
        'glass-light': 'linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.25) 100%)',
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        card: "40px",
        input: "24px",
        glass: "34px",
      },
      boxShadow: {
        'glass-dark': [
          'inset 0 1px 0 rgba(255, 255, 255, 0.1)',
          '0 8px 32px rgba(0, 0, 0, 0.3)',
          '0 4px 16px rgba(0, 0, 0, 0.2)'
        ].join(', '),
        'glass-light': [
          'inset 0 1px 0 rgba(255, 255, 255, 0.8)',
          '0 8px 32px rgba(0, 0, 0, 0.1)',
          '0 4px 16px rgba(0, 0, 0, 0.05)'
        ].join(', '),
        glass: 'inset -30px -30px 50px rgba(255,255,255,0.7), inset 30px 30px 50px rgba(13,39,80,0.16)',
      },
      dropShadow: {
        glass: [
          '-30px -30px 48px rgba(255, 255, 255, 0.7)',
          '30px 30px 48px rgba(0, 0, 0, 0.25)'
        ]
      },
      fontSize: {
        headline: 'clamp(3rem, 7vw, 6rem)',
        'headline-sm': 'clamp(2rem, 5vw, 3.5rem)',
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "glass-shine": {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        "fade-in-up": {
          '0%': { 
            opacity: '0',
            transform: 'translateY(30px)'
          },
          '100%': { 
            opacity: '1',
            transform: 'translateY(0)'
          },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "glass-shine": "glass-shine 2s ease-in-out infinite",
        "fade-in-up": "fade-in-up 0.6s ease-out forwards",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config

export default config 