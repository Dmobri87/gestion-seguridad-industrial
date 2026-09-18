/**
 * Utilidades para almacenamiento local
 */

const PREFIX = 'seguridad_industrial_';

/**
 * Guarda un valor en localStorage con prefijo
 * @param key - Clave
 * @param value - Valor a guardar
 */
export const setStorage = <T>(key: string, value: T): void => {
  try {
    const serialized = JSON.stringify(value);
    localStorage.setItem(`${PREFIX}${key}`, serialized);
  } catch (error) {
    console.error('Error saving to localStorage:', error);
  }
};

/**
 * Obtiene un valor de localStorage
 * @param key - Clave
 * @param defaultValue - Valor por defecto si no existe
 */
export const getStorage = <T>(key: string, defaultValue: T | null = null): T | null => {
  try {
    const item = localStorage.getItem(`${PREFIX}${key}`);
    if (item === null) return defaultValue;
    return JSON.parse(item) as T;
  } catch (error) {
    console.error('Error reading from localStorage:', error);
    return defaultValue;
  }
};

/**
 * Elimina un valor de localStorage
 * @param key - Clave
 */
export const removeStorage = (key: string): void => {
  try {
    localStorage.removeItem(`${PREFIX}${key}`);
  } catch (error) {
    console.error('Error removing from localStorage:', error);
  }
};

/**
 * Limpia todo el localStorage de la aplicación
 */
export const clearStorage = (): void => {
  try {
    const keys = Object.keys(localStorage);
    keys.forEach((key) => {
      if (key.startsWith(PREFIX)) {
        localStorage.removeItem(key);
      }
    });
  } catch (error) {
    console.error('Error clearing localStorage:', error);
  }
};

/**
 * Guarda un valor en sessionStorage con prefijo
 * @param key - Clave
 * @param value - Valor a guardar
 */
export const setSessionStorage = <T>(key: string, value: T): void => {
  try {
    const serialized = JSON.stringify(value);
    sessionStorage.setItem(`${PREFIX}${key}`, serialized);
  } catch (error) {
    console.error('Error saving to sessionStorage:', error);
  }
};

/**
 * Obtiene un valor de sessionStorage
 * @param key - Clave
 * @param defaultValue - Valor por defecto si no existe
 */
export const getSessionStorage = <T>(key: string, defaultValue: T | null = null): T | null => {
  try {
    const item = sessionStorage.getItem(`${PREFIX}${key}`);
    if (item === null) return defaultValue;
    return JSON.parse(item) as T;
  } catch (error) {
    console.error('Error reading from sessionStorage:', error);
    return defaultValue;
  }
};

/**
 * Elimina un valor de sessionStorage
 * @param key - Clave
 */
export const removeSessionStorage = (key: string): void => {
  try {
    sessionStorage.removeItem(`${PREFIX}${key}`);
  } catch (error) {
    console.error('Error removing from sessionStorage:', error);
  }
};

// Claves predefinidas para consistencia
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  USER: 'user',
  THEME: 'theme',
  LANGUAGE: 'language',
  SIDEBAR_COLLAPSED: 'sidebar_collapsed',
  FILTERS: 'filters',
  RECENT_SEARCHES: 'recent_searches',
  DASHBOARD_LAYOUT: 'dashboard_layout',
} as const;
