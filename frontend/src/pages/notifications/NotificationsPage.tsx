import { useEffect, useState } from 'react';
import { Badge, Button, Card, Popconfirm, Select, Space, Table, Tag, Typography, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  CheckOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { notificationsApi } from '../../services/api';
import { formatDateTime, formatRelativeTime } from '../../utils';

const { Title, Text } = Typography;

interface NotificationItem {
  id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  priority: string;
  created_at: string;
}

const getTypeTag = (type: string) => {
  if (type === 'success') return <Tag icon={<CheckCircleOutlined />} color="success">Success</Tag>;
  if (type === 'warning') return <Tag icon={<WarningOutlined />} color="warning">Warning</Tag>;
  if (type === 'error') return <Tag icon={<ExclamationCircleOutlined />} color="error">Error</Tag>;
  return <Tag icon={<InfoCircleOutlined />} color="processing">Info</Tag>;
};

const NotificationsPage = () => {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState<'all' | 'unread'>('all');
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);

  const loadNotifications = async (targetPage = page, targetPageSize = pageSize) => {
    setLoading(true);
    try {
      const response = await notificationsApi.getAll({
        page: targetPage,
        page_size: targetPageSize,
        unread_only: statusFilter === 'unread',
        type: typeFilter,
      });

      setItems(response.items || []);
      setTotal(response.total || 0);
      setPage(response.page || targetPage);
      setPageSize(response.page_size || targetPageSize);
    } catch (error) {
      console.error('Error loading notifications:', error);
      message.error('No se pudieron cargar las notificaciones');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications(1, pageSize);
  }, [statusFilter, typeFilter]);

  const handleMarkAsRead = async (id: number) => {
    try {
      await notificationsApi.markAsRead(id);
      message.success('Notificacion marcada como leida');
      loadNotifications(page, pageSize);
    } catch (error) {
      console.error('Error marking notification as read:', error);
      message.error('No se pudo actualizar la notificacion');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await notificationsApi.delete(id);
      message.success('Notificacion eliminada');
      loadNotifications(page, pageSize);
    } catch (error) {
      console.error('Error deleting notification:', error);
      message.error('No se pudo eliminar la notificacion');
    }
  };

  const columns: ColumnsType<NotificationItem> = [
    {
      title: 'Estado',
      key: 'is_read',
      width: 100,
      render: (_, record) =>
        record.is_read ? <Tag>Leida</Tag> : <Tag color="green"><Badge status="processing" /> No leida</Tag>,
    },
    {
      title: 'Tipo',
      dataIndex: 'type',
      key: 'type',
      width: 130,
      render: (value: string) => getTypeTag(value),
    },
    {
      title: 'Titulo',
      dataIndex: 'title',
      key: 'title',
      render: (value: string, record) => (
        <Text strong={!record.is_read}>{value}</Text>
      ),
    },
    {
      title: 'Mensaje',
      dataIndex: 'message',
      key: 'message',
      render: (value: string) => (
        <Text type="secondary">{value}</Text>
      ),
    },
    {
      title: 'Fecha',
      key: 'created_at',
      width: 180,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text>{formatDateTime(record.created_at)}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {formatRelativeTime(record.created_at)}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          {!record.is_read && (
            <Button
              size="small"
              icon={<CheckOutlined />}
              onClick={() => handleMarkAsRead(record.id)}
            >
              Leer
            </Button>
          )}
          <Popconfirm
            title="Eliminar notificacion"
            description="Esta accion no se puede deshacer."
            okText="Eliminar"
            cancelText="Cancelar"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card>
        <Title level={4} style={{ margin: 0 }}>Notificaciones</Title>
        <Text type="secondary">Gestiona tus notificaciones in-app y alertas activas.</Text>
      </Card>

      <Card>
        <Space style={{ marginBottom: 16 }} wrap>
          <Select
            value={statusFilter}
            onChange={(value) => setStatusFilter(value)}
            options={[
              { value: 'all', label: 'Todas' },
              { value: 'unread', label: 'No leidas' },
            ]}
            style={{ width: 160 }}
          />
          <Select
            allowClear
            placeholder="Filtrar por tipo"
            value={typeFilter}
            onChange={(value) => setTypeFilter(value)}
            options={[
              { value: 'info', label: 'Info' },
              { value: 'warning', label: 'Warning' },
              { value: 'error', label: 'Error' },
              { value: 'success', label: 'Success' },
            ]}
            style={{ width: 180 }}
          />
        </Space>

        <Table
            rowKey="id"
            loading={loading}
            dataSource={items}
            columns={columns}
            scroll={{ x: 500 }}
            pagination={{
              current: page,
            pageSize,
            total,
            showSizeChanger: true,
            onChange: (nextPage, nextPageSize) => {
              loadNotifications(nextPage, nextPageSize);
            },
          }}
        />
      </Card>
    </Space>
  );
};

export default NotificationsPage;
