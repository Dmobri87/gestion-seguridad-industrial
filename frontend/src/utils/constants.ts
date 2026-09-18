/**
 * Constantes de la aplicación
 */

// Roles del sistema
export const USER_ROLES = {
  ADMIN: 'Administrador',
  COORDINATOR: 'Coordinador',
  SUPERVISOR: 'Supervisor',
  TAE: 'TAE',
  PSE: 'PSE',
  PARAMEDIC: 'Paramedico',
  EMPLOYEE: 'Empleado',
  GUEST: 'Invitado',
} as const;

export type UserRoleType = (typeof USER_ROLES)[keyof typeof USER_ROLES];

// Estados de actividades
export const ACTIVITY_STATUS = {
  PENDING: 'Pendiente',
  IN_PROGRESS: 'En progreso',
  COMPLETED: 'Completado',
  CANCELLED: 'Cancelado',
} as const;

// Estados de ejecución
export const EXECUTION_STATUS = {
  PENDING: 'Pendiente',
  COMPLETED: 'Completado',
  WITH_NOVELTY: 'Con Novedad',
  CANCELLED: 'Cancelado',
} as const;

// Estados de aprobación
export const APPROVAL_STATUS = {
  PENDING: 'Pendiente',
  APPROVED: 'Aprobado',
  REJECTED: 'Rechazado',
} as const;

// Estados de plan mensual
export const PLAN_STATUS = {
  DRAFT: 'Borrador',
  APPROVED: 'Aprobado',
  IN_PROGRESS: 'En Progreso',
  COMPLETED: 'Completado',
} as const;

// Estados de equipos
export const EQUIPMENT_STATUS = {
  OPERATIVE: 'Operativo',
  MAINTENANCE: 'En Mantenimiento',
  OUT_OF_SERVICE: 'Fuera de Servicio',
  DECOMMISSIONED: 'Dado de Baja',
} as const;

// Estados de emergencia
export const EMERGENCY_STATUS = {
  REPORTED: 'Reportada',
  ATTENDING: 'En Atención',
  CONTROLLED: 'Controlada',
  CLOSED: 'Cerrada',
  ESCALATED: 'Escalada',
} as const;

// Severidad de emergencia
export const EMERGENCY_SEVERITY = {
  LOW: 'Baja',
  MEDIUM: 'Media',
  HIGH: 'Alta',
  CRITICAL: 'Critica',
} as const;

// Estados de certificación
export const CERTIFICATION_STATUS = {
  ACTIVE: 'Vigente',
  EXPIRING_SOON: 'Por Vencer',
  EXPIRED: 'Vencido',
  PENDING: 'Pendiente',
} as const;

// Turnos
export const SHIFTS = {
  DAY: 'Día',
  NIGHT: 'Noche',
  BOTH: 'Ambos',
} as const;

// Categorías de actividades (colores)
export const ACTIVITY_CATEGORY_COLORS: Record<string, string> = {
  'PREV': '#1890ff', // Prevención - Azul
  'EMER': '#ff4d4f', // Emergencias - Rojo
  'MANT': '#52c41a', // Mantenimiento - Verde
  'INSP': '#722ed1', // Inspección - Morado
  'CAP': '#fa8c16',  // Capacitación - Naranja
  'ADM': '#13c2c2',  // Administrativo - Cyan
  'PREP': '#eb2f96', // Preparación - Magenta
  'EVAL': '#faad14', // Evaluación - Amarillo
};

// Límites de archivo
export const FILE_LIMITS = {
  MAX_SIZE_MB: 10,
  MAX_SIZE_BYTES: 10 * 1024 * 1024,
  ALLOWED_EXTENSIONS: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'mp4', 'mov', 'avi'],
  IMAGE_EXTENSIONS: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
  DOCUMENT_EXTENSIONS: ['pdf', 'doc', 'docx', 'xls', 'xlsx'],
  VIDEO_EXTENSIONS: ['mp4', 'mov', 'avi'],
} as const;

// Configuración de paginación
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
} as const;

// Mensajes de error comunes
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Error de conexión. Verifique su conexión a internet.',
  UNAUTHORIZED: 'Sesión expirada. Por favor inicie sesión nuevamente.',
  FORBIDDEN: 'No tiene permisos para realizar esta acción.',
  NOT_FOUND: 'El recurso solicitado no fue encontrado.',
  VALIDATION_ERROR: 'Por favor verifique los datos ingresados.',
  SERVER_ERROR: 'Error interno del servidor. Intente nuevamente.',
  UNKNOWN_ERROR: 'Ha ocurrido un error inesperado.',
} as const;

// Mensajes de éxito comunes
export const SUCCESS_MESSAGES = {
  CREATED: 'Registro creado exitosamente.',
  UPDATED: 'Registro actualizado exitosamente.',
  DELETED: 'Registro eliminado exitosamente.',
  SAVED: 'Cambios guardados exitosamente.',
  APPROVED: 'Aprobación realizada exitosamente.',
  REJECTED: 'Rechazo registrado exitosamente.',
} as const;

// Colores del tema
export const THEME_COLORS = {
  PRIMARY: '#1890ff',
  SUCCESS: '#52c41a',
  WARNING: '#faad14',
  ERROR: '#ff4d4f',
  INFO: '#1890ff',
} as const;

// Breakpoints para responsive
export const BREAKPOINTS = {
  XS: 480,
  SM: 576,
  MD: 768,
  LG: 992,
  XL: 1200,
  XXL: 1600,
} as const;

// Duración de animaciones (ms)
export const ANIMATION_DURATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
} as const;

// Tiempo de expiración (ms)
export const TIMEOUTS = {
  DEBOUNCE: 300,
  TOAST: 3000,
  REDIRECT: 1500,
  SESSION_WARNING: 5 * 60 * 1000, // 5 minutos antes de expirar
} as const;
