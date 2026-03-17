/**
 * Configuration constants for Diagramik frontend
 * Centralized configuration to avoid scattering hardcoded values
 */

export const CONFIG = {
  // API Configuration
  API: {
    BASE_URL: import.meta.env.PROD ? 'https://diagramik.com' : 'http://localhost:8000',
    TIMEOUT: 30000, // 30 seconds
  },

  // OAuth Configuration
  OAUTH: {
    GOOGLE_CLIENT_ID:
      import.meta.env.PUBLIC_GOOGLE_CLIENT_ID ||
      '904069135998-4h84vjsjnjvo5d442gsqvlummq6ebdj3.apps.googleusercontent.com',
  },

  // Auth Storage
  AUTH: {
    STORAGE_KEY: 'diagramik_auth',
  },

  // Validation
  VALIDATION: {
    NAME_MAX_LENGTH: 100,
    EMAIL_MAX_LENGTH: 254,
    PASSWORD_MIN_LENGTH: 8,
  },

  // UI Constraints
  UI: {
    DIAGRAM_TITLE_MAX_LENGTH: 255,
    PROMPT_MAX_LENGTH: 5000,
    RESIZABLE_MIN_PERCENT: 15,
    RESIZABLE_MAX_PERCENT: 85,
    RESIZE_STEP_SMALL: 5, // percentage
    RESIZE_STEP_LARGE: 10, // percentage (with Shift)
  },

  // Timeouts & Delays
  TIMERS: {
    DEBOUNCE_SEARCH: 300,
    DEBOUNCE_RESIZE: 100,
    TOAST_DURATION: 5000,
  },
} as const;
