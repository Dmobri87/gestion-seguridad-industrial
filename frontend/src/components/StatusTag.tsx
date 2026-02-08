import React from 'react';
import { Tag } from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  SyncOutlined,
  MinusCircleOutlined,
} from '@ant-design/icons';

type StatusType =
  | 'success' | 'active' | 'completed' | 'approved' | 'vigente'
  | 'warning' | 'pending' | 'in_progress' | 'por_vencer'
  | 'error' | 'rejected' | 'expired' | 'vencido' | 'cancelled'
  | 'default' | 'draft' | 'inactive';

interface StatusTagProps {
  status: string;
  text?: string;
  showIcon?: boolean;
  size?: 'small' | 'default';
}

/**
 * StatusTag - Componente para mostrar estados con colores e iconos consistentes
 *
 * Mapea automáticamente estados comunes a colores e iconos apropiados.
 *
 * Uso:
 * <StatusTag status="completed" />
 * <StatusTag status="pending" text="En espera" showIcon />
 */
export const StatusTag: React.FC<StatusTagProps> = ({
  status,
  text,
  showIcon = false,
  size = 'default',
}) => {
  const normalizedStatus = status.toLowerCase().replace(/\s+/g, '_') as StatusType;

  const getConfig = (): { color: string; icon: React.ReactNode; label: string } => {
    switch (normalizedStatus) {
      // Success states
      case 'success':
      case 'active':
      case 'completed':
      case 'approved':
      case 'vigente':
        return {
          color: 'success',
          icon: <CheckCircleOutlined />,
          label: text || 'Completado',
        };

      // Warning states
      case 'warning':
      case 'pending':
      case 'por_vencer':
        return {
          color: 'warning',
          icon: <ExclamationCircleOutlined />,
          label: text || 'Pendiente',
        };

      // Processing states
      case 'in_progress':
        return {
          color: 'processing',
          icon: <SyncOutlined spin />,
          label: text || 'En progreso',
        };

      // Error states
      case 'error':
      case 'rejected':
      case 'expired':
      case 'vencido':
      case 'cancelled':
        return {
          color: 'error',
          icon: <CloseCircleOutlined />,
          label: text || 'Error',
        };

      // Default states
      case 'default':
      case 'draft':
      case 'inactive':
      default:
        return {
          color: 'default',
          icon: <MinusCircleOutlined />,
          label: text || status,
        };
    }
  };

  const config = getConfig();

  return (
    <Tag
      color={config.color}
      icon={showIcon ? config.icon : undefined}
      style={size === 'small' ? { fontSize: 12, padding: '0 4px' } : undefined}
    >
      {config.label}
    </Tag>
  );
};
