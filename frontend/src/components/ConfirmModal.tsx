import React from 'react';
import { Modal, ModalProps } from 'antd';
import { ExclamationCircleOutlined, CheckCircleOutlined, InfoCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';

type ConfirmType = 'confirm' | 'info' | 'success' | 'error' | 'warning';

interface ConfirmModalProps extends Omit<ModalProps, 'onOk' | 'onCancel'> {
  type?: ConfirmType;
  title: string;
  content: React.ReactNode;
  onConfirm: () => void | Promise<void>;
  onCancel?: () => void;
  confirmText?: string;
  cancelText?: string;
  loading?: boolean;
  danger?: boolean;
}

/**
 * ConfirmModal - Modal de confirmación reutilizable
 *
 * Uso:
 * <ConfirmModal
 *   open={showModal}
 *   type="warning"
 *   title="¿Eliminar registro?"
 *   content="Esta acción no se puede deshacer."
 *   onConfirm={handleDelete}
 *   onCancel={() => setShowModal(false)}
 *   danger
 * />
 */
export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  type = 'confirm',
  title,
  content,
  onConfirm,
  onCancel,
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  loading = false,
  danger = false,
  ...props
}) => {
  const getIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 22 }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 22 }} />;
      case 'info':
        return <InfoCircleOutlined style={{ color: '#1890ff', fontSize: 22 }} />;
      case 'warning':
      case 'confirm':
      default:
        return <ExclamationCircleOutlined style={{ color: '#faad14', fontSize: 22 }} />;
    }
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {getIcon()}
          <span>{title}</span>
        </div>
      }
      onOk={onConfirm}
      onCancel={onCancel}
      okText={confirmText}
      cancelText={cancelText}
      okButtonProps={{
        loading,
        danger: danger || type === 'error',
      }}
      centered
      {...props}
    >
      {content}
    </Modal>
  );
};

/**
 * Función helper para mostrar confirmación rápida usando Modal.confirm
 *
 * Uso:
 * showConfirm({
 *   title: '¿Eliminar?',
 *   content: 'Esta acción no se puede deshacer',
 *   onConfirm: () => deleteItem(id),
 *   danger: true,
 * });
 */
export const showConfirm = ({
  type = 'confirm',
  title,
  content,
  onConfirm,
  onCancel,
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  danger = false,
}: Omit<ConfirmModalProps, 'open'>) => {
  const getModalMethod = () => {
    switch (type) {
      case 'success':
        return Modal.success;
      case 'error':
        return Modal.error;
      case 'info':
        return Modal.info;
      case 'warning':
        return Modal.warning;
      default:
        return Modal.confirm;
    }
  };

  getModalMethod()({
    title,
    content,
    okText: confirmText,
    cancelText,
    okButtonProps: { danger },
    onOk: onConfirm,
    onCancel,
    centered: true,
  });
};
