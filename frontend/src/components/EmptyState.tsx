import React from 'react';
import { Empty, Button, Typography } from 'antd';
import { PlusOutlined, SearchOutlined, InboxOutlined } from '@ant-design/icons';

const { Text } = Typography;

type EmptyType = 'default' | 'search' | 'data' | 'error';

interface EmptyStateProps {
  type?: EmptyType;
  title?: string;
  description?: string;
  image?: React.ReactNode;
  actionText?: string;
  onAction?: () => void;
  showAction?: boolean;
}

/**
 * EmptyState - Componente para estados vacíos
 *
 * Uso:
 * <EmptyState
 *   type="search"
 *   title="Sin resultados"
 *   description="No se encontraron registros con los filtros aplicados"
 * />
 *
 * <EmptyState
 *   type="data"
 *   title="Sin datos"
 *   actionText="Crear nuevo"
 *   onAction={() => setShowModal(true)}
 * />
 */
export const EmptyState: React.FC<EmptyStateProps> = ({
  type = 'default',
  title,
  description,
  image,
  actionText,
  onAction,
  showAction = true,
}) => {
  const getConfig = () => {
    switch (type) {
      case 'search':
        return {
          image: <SearchOutlined style={{ fontSize: 64, color: '#bfbfbf' }} />,
          title: title || 'Sin resultados',
          description: description || 'No se encontraron registros con los criterios de búsqueda.',
          actionText: actionText || 'Limpiar filtros',
          actionIcon: <SearchOutlined />,
        };
      case 'data':
        return {
          image: <InboxOutlined style={{ fontSize: 64, color: '#bfbfbf' }} />,
          title: title || 'Sin datos',
          description: description || 'Aún no hay registros. Comienza creando uno nuevo.',
          actionText: actionText || 'Crear nuevo',
          actionIcon: <PlusOutlined />,
        };
      case 'error':
        return {
          image: Empty.PRESENTED_IMAGE_SIMPLE,
          title: title || 'Error al cargar',
          description: description || 'No se pudieron cargar los datos. Intenta de nuevo.',
          actionText: actionText || 'Reintentar',
          actionIcon: undefined,
        };
      default:
        return {
          image: Empty.PRESENTED_IMAGE_DEFAULT,
          title: title || 'Sin datos',
          description: description || 'No hay información disponible.',
          actionText: actionText,
          actionIcon: undefined,
        };
    }
  };

  const config = getConfig();

  return (
    <Empty
      image={image || config.image}
      imageStyle={{ height: 80 }}
      description={
        <div style={{ textAlign: 'center' }}>
          <Text strong style={{ display: 'block', marginBottom: 8, fontSize: 16 }}>
            {config.title}
          </Text>
          <Text type="secondary">{config.description}</Text>
        </div>
      }
    >
      {showAction && onAction && config.actionText && (
        <Button
          type="primary"
          icon={config.actionIcon}
          onClick={onAction}
        >
          {config.actionText}
        </Button>
      )}
    </Empty>
  );
};
