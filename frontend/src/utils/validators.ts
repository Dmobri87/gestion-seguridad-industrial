/**
 * Validadores para formularios y datos
 */

/**
 * Valida un email
 * @param email - Email a validar
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Valida una contraseña fuerte
 * Requisitos: mínimo 8 caracteres, una mayúscula, una minúscula, un número
 * @param password - Contraseña a validar
 */
export const isStrongPassword = (password: string): {
  isValid: boolean;
  errors: string[];
} => {
  const errors: string[] = [];

  if (password.length < 8) {
    errors.push('Mínimo 8 caracteres');
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('Al menos una letra mayúscula');
  }
  if (!/[a-z]/.test(password)) {
    errors.push('Al menos una letra minúscula');
  }
  if (!/[0-9]/.test(password)) {
    errors.push('Al menos un número');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Valida un número de teléfono colombiano
 * @param phone - Teléfono a validar
 */
export const isValidPhone = (phone: string): boolean => {
  const cleaned = phone.replace(/\D/g, '');
  // 10 dígitos para Colombia
  return cleaned.length === 10 && /^3\d{9}$/.test(cleaned);
};

/**
 * Valida un código de empleado
 * @param code - Código a validar
 */
export const isValidEmployeeCode = (code: string): boolean => {
  // Formato: letras y números, 3-20 caracteres
  return /^[A-Za-z0-9]{3,20}$/.test(code);
};

/**
 * Valida que un valor esté en un rango
 * @param value - Valor a validar
 * @param min - Mínimo
 * @param max - Máximo
 */
export const isInRange = (value: number, min: number, max: number): boolean => {
  return value >= min && value <= max;
};

/**
 * Valida una fecha no sea futura
 * @param date - Fecha a validar
 */
export const isNotFutureDate = (date: Date | string): boolean => {
  const inputDate = new Date(date);
  const today = new Date();
  today.setHours(23, 59, 59, 999);
  return inputDate <= today;
};

/**
 * Valida que una fecha esté dentro de los últimos N días
 * @param date - Fecha a validar
 * @param days - Número de días hacia atrás
 */
export const isWithinLastDays = (date: Date | string, days: number): boolean => {
  const inputDate = new Date(date);
  const limitDate = new Date();
  limitDate.setDate(limitDate.getDate() - days);
  return inputDate >= limitDate;
};

/**
 * Valida un archivo por extensión
 * @param filename - Nombre del archivo
 * @param allowedExtensions - Extensiones permitidas
 */
export const isValidFileExtension = (
  filename: string,
  allowedExtensions: string[]
): boolean => {
  const extension = filename.split('.').pop()?.toLowerCase() || '';
  return allowedExtensions.includes(extension);
};

/**
 * Valida un archivo por tamaño
 * @param sizeInBytes - Tamaño en bytes
 * @param maxSizeInMB - Tamaño máximo en MB
 */
export const isValidFileSize = (sizeInBytes: number, maxSizeInMB: number): boolean => {
  return sizeInBytes <= maxSizeInMB * 1024 * 1024;
};

/**
 * Reglas de validación para Ant Design Form
 */
export const validationRules = {
  required: (message = 'Este campo es requerido') => ({
    required: true,
    message,
  }),

  email: (message = 'Ingrese un email válido') => ({
    type: 'email' as const,
    message,
  }),

  minLength: (min: number, message?: string) => ({
    min,
    message: message || `Mínimo ${min} caracteres`,
  }),

  maxLength: (max: number, message?: string) => ({
    max,
    message: message || `Máximo ${max} caracteres`,
  }),

  pattern: (pattern: RegExp, message: string) => ({
    pattern,
    message,
  }),

  phone: (message = 'Ingrese un teléfono válido (10 dígitos)') => ({
    pattern: /^3\d{9}$/,
    message,
  }),

  employeeCode: (message = 'Código inválido (solo letras y números, 3-20 caracteres)') => ({
    pattern: /^[A-Za-z0-9]{3,20}$/,
    message,
  }),
};
