// Design tokens for Vendor Routing Platform Observability Dashboard
export const tokens = {
  colors: {
    background: '#0E0F11', // Near-black background
    panel: '#16181C',      // Panel surface
    border: '#24272E',      // Muted border
    text: '#E6E8EB',        // Light off-white text
    muted: '#8B9099',       // Cool gray muted text
    accent: '#6366F1',      // Night indigo accent/CTA
    
    // Status colors
    success: '#3FB950',     // Signal green
    warning: '#D29922',     // Warn amber
    danger: '#F85149',      // Danger red
    inactive: '#484F58'     // Muted gray for disabled state
  },
  fonts: {
    ui: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    mono: '"JetBrains Mono", "IBM Plex Mono", "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace'
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    xxl: '32px'
  },
  radius: {
    sm: '4px',
    md: '6px',
    lg: '8px'
  }
};
