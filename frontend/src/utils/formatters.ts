import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/es';

dayjs.extend(relativeTime);
dayjs.locale('es');

/**
 * Formatea una fecha en formato legible
 * @param date - Fecha a formatear (string, Date, o dayjs)
 * @param format - Formato de salida (default: 'DD/MM/YYYY')
 */
export const formatDate = (
  date: string | Date | null | undefined,
  format = 'DD/MM/YYYY'
): string => {
  if (!date) return '-';
  return dayjs(date).format(format);
};

/**
 * Formatea una fecha con hora
 * @param date - Fecha a formatear
 */
export const formatDateTime = (date: string | Date | null | undefined): string => {
  return formatDate(date, 'DD/MM/YYYY HH:mm');
};

/**
 * Formatea una fecha en formato relativo (hace 2 horas, hace 3 días, etc.)
 * @param date - Fecha a formatear
 */
export const formatRelativeTime = (date: string | Date | null | undefined): string => {
  if (!date) return '-';
  return dayjs(date).fromNow();
};

/**
 * Formatea un número como moneda
 * @param value - Valor numérico
 * @param currency - Código de moneda (default: 'COP')
 */
export const formatCurrency = (
  value: number | null | undefined,
  currency = 'COP'
): string => {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

/**
 * Formatea un número con separadores de miles
 * @param value - Valor numérico
 * @param decimals - Cantidad de decimales (default: 0)
 */
export const formatNumber = (
  value: number | null | undefined,
  decimals = 0
): string => {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('es-CO', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

/**
 * Formatea un porcentaje
 * @param value - Valor numérico (0-100 o 0-1)
 * @param decimals - Cantidad de decimales
 * @param isDecimal - Si el valor está en formato decimal (0-1)
 */
export const formatPercentage = (
  value: number | null | undefined,
  decimals = 1,
  isDecimal = false
): string => {
  if (value === null || value === undefined) return '-';
  const percentage = isDecimal ? value * 100 : value;
  return `${percentage.toFixed(decimals)}%`;
};

/**
 * Formatea un tiempo de respuesta en minutos a formato legible
 * @param minutes - Tiempo en minutos
 */
export const formatResponseTime = (minutes: number | null | undefined): string => {
  if (minutes === null || minutes === undefined) return '-';
  if (minutes < 60) {
    return `${Math.round(minutes)} min`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
};

/**
 * Formatea un tamaño de archivo en bytes a formato legible
 * @param bytes - Tamaño en bytes
 */
export const formatFileSize = (bytes: number | null | undefined): string => {
  if (bytes === null || bytes === undefined) return '-';
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
};

/**
 * Formatea un código de empleado o documento
 * @param code - Código a formatear
 */
export const formatCode = (code: string | null | undefined): string => {
  if (!code) return '-';
  return code.toUpperCase();
};

/**
 * Trunca un texto largo
 * @param text - Texto a truncar
 * @param maxLength - Longitud máxima
 */
export const truncateText = (
  text: string | null | undefined,
  maxLength = 50
): string => {
  if (!text) return '-';
  if (text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
};

/**
 * Formatea un nombre completo (capitalización correcta)
 * @param name - Nombre a formatear
 */
export const formatName = (name: string | null | undefined): string => {
  if (!name) return '-';
  return name
    .toLowerCase()
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Formatea un número de teléfono colombiano
 * @param phone - Número de teléfono
 */
export const formatPhone = (phone: string | null | undefined): string => {
  if (!phone) return '-';
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  return phone;
};

/**
 * Formatea un countdown en segundos a MM:SS
 * @param seconds - Segundos restantes
 */
export const formatCountdown = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};
