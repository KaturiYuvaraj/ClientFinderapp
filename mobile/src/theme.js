// Retro parchment theme tokens for React Native
export const colors = {
  // Backgrounds
  bgPage:       '#f5f0e8',
  bgCard:       '#fdf8f0',
  bgElevated:   '#ede5d5',
  bgActive:     '#f0e8d8',

  // Borders
  borderSubtle: '#d4c9b4',
  borderMedium: '#b8a88a',
  borderDark:   '#8b7355',

  // Text
  textPrimary:  '#1a0f00',
  textSecondary:'#4a3728',
  textMuted:    '#7a6555',

  // Brand / Primary
  primary:      '#8b1a1a',
  primaryDark:  '#5c1010',
  primaryLight: '#f5e8e8',

  // Accents
  emerald:      '#1a5c3a',
  emeraldLight: '#e8f5ee',
  amber:        '#7a4a00',
  amberLight:   '#fdf3e0',
  cyan:         '#1a4a5c',
  cyanLight:    '#e8f5fc',
  purple:       '#1a1a5c',
  purpleLight:  '#e8e8f5',

  // Status
  white:        '#ffffff',
  danger:       '#8b1a1a',
};

export const typography = {
  display:     { fontFamily: undefined, fontWeight: '700' }, // system serif fallback
  body:        { fontFamily: undefined, fontWeight: '400' },
  label:       { fontFamily: undefined, fontWeight: '400', letterSpacing: 0.8 },
  mono:        { fontFamily: 'monospace' },
};

export const radius = {
  xs: 2,
  sm: 4,
  md: 6,
  lg: 10,
  full: 999,
};

export const shadows = {
  xs: {
    shadowColor: '#1a0f00',
    shadowOffset: { width: 2, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 0,
    elevation: 2,
  },
  sm: {
    shadowColor: '#1a0f00',
    shadowOffset: { width: 3, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 0,
    elevation: 3,
  },
  md: {
    shadowColor: '#1a0f00',
    shadowOffset: { width: 4, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 0,
    elevation: 5,
  },
};
