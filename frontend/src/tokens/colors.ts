export const palette = {
  common: {
    black: '#000',
    white: '#FFF',
  },
  green: {
    DEFAULT: '#2CC966', // Bright green from "Начать бесплатно" button
    light: '#48D982',
    dark: '#1FB653',
  },
  grey: {
    dark: '#0D1117',     // Main background
    medium: '#161B22',   // Card background (solid part, if any)
    light: '#21262D',    // Borders, dividers
    ultraDark: '#0A0E13', // For gradients
  },
  // AICODE-NOTE: Added gradient colors for background
  gradient: {
    dark: {
      from: '#000000',      // Pure black
      to: '#1a1a1a',       // Dark grey closer to black
      via: '#0d1117',      // Middle gradient point
    },
    light: {
      from: '#ffffff',      // Pure white
      to: '#f8fafc',       // Very light grey
      via: '#f1f5f9',      // Middle gradient point
    }
  },
  glass: {
    dark: {
      bg: 'rgba(255, 255, 255, 0.05)',      // Glass background for dark theme
      border: 'rgba(255, 255, 255, 0.1)',   // Glass border for dark theme
      shadow: {
        inner: 'rgba(255, 255, 255, 0.1)',  // Inner highlight
        drop: 'rgba(0, 0, 0, 0.3)',         // Drop shadow
      }
    },
    light: {
      bg: 'rgba(255, 255, 255, 0.25)',      // Glass background for light theme
      border: 'rgba(255, 255, 255, 0.3)',   // Glass border for light theme
      shadow: {
        inner: 'rgba(255, 255, 255, 0.8)',  // Inner highlight
        drop: 'rgba(0, 0, 0, 0.1)',         // Drop shadow
      }
    }
  },
  text: {
    primary: '#E6EDF3',   // Main text color
    secondary: '#8B949E', // Lighter text
  },
}; 