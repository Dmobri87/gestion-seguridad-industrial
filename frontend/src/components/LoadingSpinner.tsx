import React from 'react';
import { Spin, SpinProps } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

interface LoadingSpinnerProps extends SpinProps {
  fullScreen?: boolean;
  text?: string;
}

/**
 * LoadingSpinner - Componente de carga centralizado
 *
 * Uso:
 * <LoadingSpinner />
 * <LoadingSpinner fullScreen text="Cargando datos..." />
 */
export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  fullScreen = false,
  text,
  size = 'large',
  ...props
}) => {
  const antIcon = <LoadingOutlined style={{ fontSize: size === 'large' ? 48 : 24 }} spin />;

  if (fullScreen) {
    return (
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(255, 255, 255, 0.9)',
          zIndex: 9999,
        }}
      >
        <Spin indicator={antIcon} size={size} {...props} />
        {text && (
          <p style={{ marginTop: 16, color: '#666', fontSize: 14 }}>{text}</p>
        )}
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 40,
      }}
    >
      <Spin indicator={antIcon} size={size} {...props} />
      {text && (
        <p style={{ marginTop: 16, color: '#666', fontSize: 14 }}>{text}</p>
      )}
    </div>
  );
};
