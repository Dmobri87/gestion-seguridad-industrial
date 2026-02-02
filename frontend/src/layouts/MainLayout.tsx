import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Avatar, Dropdown, Space, Typography } from 'antd';
import type { MenuProps } from 'antd';
import {
  DashboardOutlined,
  CalendarOutlined,
  CheckSquareOutlined,
  AlertOutlined,
  ToolOutlined,
  SafetyCertificateOutlined,
  AppstoreOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  TeamOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../stores/authStore';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const MainLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const menuItems: MenuProps['items'] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/activities',
      icon: <AppstoreOutlined />,
      label: 'Catálogo',
    },
    {
      key: '/planning',
      icon: <CalendarOutlined />,
      label: 'Planificación',
    },
    {
      key: '/execution',
      icon: <CheckSquareOutlined />,
      label: 'Ejecución',
    },
    {
      key: '/emergencies',
      icon: <AlertOutlined />,
      label: 'Emergencias',
    },
    {
      key: '/equipment',
      icon: <ToolOutlined />,
      label: 'Equipos',
    },
    {
      key: '/certifications',
      icon: <SafetyCertificateOutlined />,
      label: 'Certificaciones',
    },
    {
      key: '/users/performance',
      icon: <TeamOutlined />,
      label: 'Desempeño TAEs',
    },
    {
      key: '/admin',
      icon: <SettingOutlined />,
      label: 'Administración',
    },
  ];

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Mi Perfil',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Cerrar Sesión',
      danger: true,
    },
  ];

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    navigate(e.key);
  };

  const handleUserMenuClick: MenuProps['onClick'] = (e) => {
    if (e.key === 'profile') {
      navigate('/profile');
    } else if (e.key === 'logout') {
      logout();
      navigate('/login');
    }
  };

  return (
    <Layout className="app-layout">
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: collapsed ? 16 : 14,
            fontWeight: 600,
            padding: '0 16px',
          }}
        >
          {collapsed ? 'SGS' : 'Seguridad Industrial'}
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>

      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'margin-left 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {collapsed ? (
              <MenuUnfoldOutlined
                style={{ fontSize: 18, cursor: 'pointer' }}
                onClick={() => setCollapsed(false)}
              />
            ) : (
              <MenuFoldOutlined
                style={{ fontSize: 18, cursor: 'pointer' }}
                onClick={() => setCollapsed(true)}
              />
            )}
          </div>

          <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenuClick }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
              <div style={{ lineHeight: 1.2 }}>
                <Text strong style={{ display: 'block' }}>{user?.full_name}</Text>
                <Text type="secondary" style={{ fontSize: 12 }}>{user?.role}</Text>
              </div>
            </Space>
          </Dropdown>
        </Header>

        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
