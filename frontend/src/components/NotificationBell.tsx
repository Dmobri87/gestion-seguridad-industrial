import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge, Button, Divider, Dropdown, Empty, List, Space, Tag, Typography, message } from 'antd';
import {
  BellOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { alertsApi, notificationsApi } from '../services/api';
import { formatRelativeTime } from '../utils';

const { Text, Title } = Typography;

interface NotificationItem {
  id: number;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success' | string;
  is_read: boolean;
  link?: string | null;
  created_at: string;
}

const getTypeIcon = (type: string) => {
  if (type === 'success') return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
  if (type === 'warning') return <WarningOutlined style={{ color: '#faad14' }} />;
  if (type === 'error') return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
  return <InfoCircleOutlined style={{ color: '#1890ff' }} />;
};

const NotificationBell = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const [listResponse, unreadResponse] = await Promise.all([
        notificationsApi.getAll({ page: 1, page_size: 10 }),
        notificationsApi.getUnreadCount(),
      ]);
      setNotifications(listResponse.items || []);
      setUnreadCount(unreadResponse.count || 0);
    } catch (error) {
      console.error('Error loading notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const boot = async () => {
      try {
        await alertsApi.checkExpirations();
      } catch (error) {
        console.error('Error checking expirations:', error);
      }
      fetchNotifications();
    };

    boot();
    const intervalId = setInterval(fetchNotifications, 30000);
    return () => clearInterval(intervalId);
  }, []);

  const handleMarkAsRead = async (item: NotificationItem) => {
    try {
      if (!item.is_read) {
        await notificationsApi.markAsRead(item.id);
      }
      await fetchNotifications();
      if (item.link) {
        navigate(item.link);
      }
    } catch (error) {
      console.error('Error marking notification as read:', error);
      message.error('No se pudo actualizar la notificacion');
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      message.success('Notificaciones marcadas como leidas');
      fetchNotifications();
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
      message.error('No se pudieron actualizar las notificaciones');
    }
  };

  const overlay = useMemo(
    () => (
      <div
        style={{
          width: 380,
          maxHeight: 460,
          background: '#fff',
          borderRadius: 8,
          boxShadow: '0 6px 18px rgba(0, 0, 0, 0.16)',
          overflow: 'hidden',
        }}
      >
        <div style={{ padding: '12px 14px', borderBottom: '1px solid #f0f0f0' }}>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Title level={5} style={{ margin: 0 }}>
              Notificaciones
            </Title>
            <Button type="link" size="small" onClick={handleMarkAllAsRead}>
              Marcar todas como leidas
            </Button>
          </Space>
        </div>

        <div style={{ maxHeight: 330, overflowY: 'auto', padding: '4px 0' }}>
          {notifications.length === 0 ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sin notificaciones" style={{ margin: '24px 0' }} />
          ) : (
            <List
              loading={loading}
              dataSource={notifications}
              renderItem={(item) => (
                <List.Item
                  style={{
                    cursor: 'pointer',
                    padding: '10px 14px',
                    background: item.is_read ? '#fff' : '#f6ffed',
                  }}
                  onClick={() => handleMarkAsRead(item)}
                >
                  <List.Item.Meta
                    avatar={getTypeIcon(item.type)}
                    title={
                      <Space>
                        <Text strong={!item.is_read}>{item.title}</Text>
                        {!item.is_read && <Tag color="green">Nueva</Tag>}
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={2}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {item.message}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {formatRelativeTime(item.created_at)}
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </div>

        <Divider style={{ margin: 0 }} />
        <div style={{ padding: 10, textAlign: 'center' }}>
          <Button
            type="link"
            onClick={() => {
              navigate('/notifications');
            }}
          >
            Ver todas
          </Button>
        </div>
      </div>
    ),
    [notifications, loading]
  );

  return (
    <Dropdown trigger={['click']} dropdownRender={() => overlay} placement="bottomRight">
      <Button type="text" style={{ border: 'none' }}>
        <Badge count={unreadCount} size="small" overflowCount={99}>
          <BellOutlined style={{ fontSize: 20 }} />
        </Badge>
      </Button>
    </Dropdown>
  );
};

export default NotificationBell;
