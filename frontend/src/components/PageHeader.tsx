import React from 'react';
import { Typography, Breadcrumb, Space, Button } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

interface BreadcrumbItem {
  title: string;
  path?: string;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  showBack?: boolean;
  backPath?: string;
  extra?: React.ReactNode;
  children?: React.ReactNode;
}

/**
 * PageHeader - Encabezado de página consistente
 *
 * Uso:
 * <PageHeader
 *   title="Gestión de Usuarios"
 *   subtitle="Administra los usuarios del sistema"
 *   breadcrumbs={[
 *     { title: 'Inicio', path: '/' },
 *     { title: 'Usuarios' },
 *   ]}
 *   extra={<Button type="primary">Nuevo Usuario</Button>}
 * />
 */
export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  breadcrumbs,
  showBack = false,
  backPath,
  extra,
  children,
}) => {
  const navigate = useNavigate();

  const handleBack = () => {
    if (backPath) {
      navigate(backPath);
    } else {
      navigate(-1);
    }
  };

  return (
    <div style={{ marginBottom: 24 }}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <Breadcrumb
          style={{ marginBottom: 16 }}
          items={breadcrumbs.map((item) => ({
            title: item.path ? (
              <a onClick={() => navigate(item.path!)}>{item.title}</a>
            ) : (
              item.title
            ),
          }))}
        />
      )}

      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <Space direction="vertical" size={4}>
          <Space align="center">
            {showBack && (
              <Button
                type="text"
                icon={<ArrowLeftOutlined />}
                onClick={handleBack}
                style={{ marginRight: 8 }}
              />
            )}
            <Title level={3} style={{ margin: 0 }}>
              {title}
            </Title>
          </Space>
          {subtitle && (
            <Text type="secondary" style={{ fontSize: 14 }}>
              {subtitle}
            </Text>
          )}
        </Space>

        {extra && <div>{extra}</div>}
      </div>

      {children && <div style={{ marginTop: 16 }}>{children}</div>}
    </div>
  );
};
