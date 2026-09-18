import React, { useState, useEffect } from 'react';
import { Layout, Menu, Drawer, Button, Avatar, Badge, Typography, theme } from 'antd';
import {
  DashboardOutlined, AppstoreOutlined, CalendarOutlined, ThunderboltOutlined,
  AlertOutlined, TeamOutlined, SafetyCertificateOutlined, BarChartOutlined,
  TrophyOutlined, SettingOutlined, UserOutlined, MenuOutlined, BellOutlined,
  LogoutOutlined, CloseOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const MOBILE_BP = 768;

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/catalogo', icon: <AppstoreOutlined />, label: 'Catálogo' },
  { key: '/planificacion', icon: <CalendarOutlined />, label: 'Planificación' },
  { key: '/ejecucion', icon: <ThunderboltOutlined />, label: 'Ejecución' },
  { key: '/emergencias', icon: <AlertOutlined />, label: 'Emergencias' },
  { key: '/equipos', icon: <TeamOutlined />, label: 'Equipos' },
  { key: '/certificaciones', icon: <SafetyCertificateOutlined />, label: 'Certificaciones' },
  { key: '/reportes', icon: <BarChartOutlined />, label: 'Reportes' },
  { key: '/desempeno', icon: <TrophyOutlined />, label: 'Desempeño TAEs' },
  { key: '/administracion', icon: <SettingOutlined />, label: 'Administración' },
  { key: '/perfil', icon: <UserOutlined />, label: 'Perfil' },
];

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const { token } = theme.useToken();

  const [isMobile, setIsMobile] = useState(window.innerWidth < MOBILE_BP);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  // Heartbeat de presencia cada 2 minutos
  useEffect(() => {
    const sendHeartbeat = () => {
      import('../services/api').then(({ usersApi }) => {
        usersApi.heartbeat(location.pathname).catch(() => {});
      });
    };
    sendHeartbeat(); // Initial
    const interval = setInterval(sendHeartbeat, 2 * 60 * 1000);
    return () => clearInterval(interval);
  }, [location.pathname]);

  const basePath = `/${location.pathname.split('/').filter(Boolean)[0] || 'dashboard'}`;
  const selectedMenuKey = menuItems.some((item) => item.key === basePath) ? basePath : '/dashboard';

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < MOBILE_BP);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
    if (isMobile) setDrawerOpen(false);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const menuContent = (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Logo */}
      <div style={{
        padding: collapsed ? '16px 12px' : '20px 16px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        background: 'linear-gradient(135deg, rgba(8,145,178,0.3) 0%, rgba(8,145,178,0.1) 100%)',
        transition: 'padding 0.2s ease',
      }}>
        <SafetyCertificateOutlined style={{ color: '#22d3ee', fontSize: 22 }} />
        {(!collapsed || isMobile) && (
          <Text strong style={{ color: '#fff', fontSize: 15, letterSpacing: '0.02em' }}>Gestión GAE</Text>
        )}
      </div>

      {/* Menu items */}
      <Menu
        mode="inline"
        selectedKeys={[selectedMenuKey]}
        onClick={handleMenuClick}
        style={{ flex: 1, borderRight: 0, overflowY: 'auto' }}
        items={menuItems}
      />

      {/* User + Logout */}
      <div style={{
        padding: '14px 16px',
        borderTop: '1px solid rgba(255,255,255,0.08)',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        cursor: 'pointer',
        transition: 'background 0.2s ease',
      }}
      onClick={handleLogout}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
      >
        <Avatar size="small" icon={<UserOutlined />} style={{ background: 'linear-gradient(135deg, #0891b2, #0e7490)' }} />
        {(!collapsed || isMobile) && (
          <Text style={{ fontSize: 12, flex: 1 }} ellipsis>
            {user?.full_name || user?.email || 'Usuario'}
          </Text>
        )}
        <LogoutOutlined style={{ color: token.colorTextSecondary, fontSize: 14 }} />
      </div>
    </div>
  );

  return (
    <Layout style={{ minHeight: '100vh', width: '100%', minWidth: 0, overflow: 'hidden' }}>
      {/* DESKTOP: Sider fijo */}
      {!isMobile && (
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          width={220}
          collapsedWidth={64}
          style={{
            height: '100vh',
            position: 'fixed',
            left: 0,
            top: 0,
            bottom: 0,
            zIndex: 100,
            overflow: 'hidden',
            background: 'linear-gradient(180deg, #0a1628 0%, #0f2035 100%)',
            borderRight: '1px solid rgba(255,255,255,0.05)',
          }}
        >
          {menuContent}
        </Sider>
      )}

      {/* MOBILE: Drawer */}
      {isMobile && (
        <Drawer
          placement="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          width={240}
          styles={{ body: { padding: 0 } }}
          closeIcon={<CloseOutlined />}
          title={null}
        >
          {menuContent}
        </Drawer>
      )}

      {/* Main layout */}
      <Layout style={{
        marginLeft: isMobile ? 0 : (collapsed ? 64 : 220),
        transition: 'margin-left 0.2s',
        minWidth: 0,
        overflow: 'hidden',
        width: isMobile ? '100%' : undefined,
      }}>
        {/* Header */}
        <Header style={{
          position: 'sticky',
          top: 0,
          zIndex: 99,
          padding: '0 20px',
          background: '#ffffff',
          borderBottom: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          height: 56,
          width: '100%',
          boxSizing: 'border-box',
        }}>
          {/* Hamburger (mobile) or collapse toggle info (desktop handled by Sider) */}
          {isMobile && (
            <Button
              type="text"
              icon={<MenuOutlined />}
              onClick={() => setDrawerOpen(true)}
              size="large"
            />
          )}

          <Text strong style={{ fontSize: 16, flex: 1 }}>Gestión GAE</Text>

          <Badge count={0} size="small">
            <Button
              type="text"
              icon={<BellOutlined style={{ fontSize: 18 }} />}
              onClick={() => navigate('/notificaciones')}
            />
          </Badge>

          <Avatar
            icon={<UserOutlined />}
            style={{ background: 'linear-gradient(135deg, #0891b2, #0e7490)', cursor: 'pointer', flexShrink: 0 }}
            onClick={() => navigate('/perfil')}
          />
        </Header>

        {/* Page content */}
        <Content style={{
          padding: isMobile ? '12px' : '24px',
          minWidth: 0,
          width: '100%',
          boxSizing: 'border-box',
          overflowX: 'hidden',
          overflowY: 'auto',
          minHeight: 'calc(100vh - 56px)',
          background: '#f0f4f8',
        }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
