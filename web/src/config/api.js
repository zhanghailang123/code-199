/**
 * API Configuration
 * Centralized API base URL for all fetch requests.
 * Uses environment variable in production, falls back to localhost for development.
 */
export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
