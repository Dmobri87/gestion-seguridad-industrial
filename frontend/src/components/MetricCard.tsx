import React from 'react';
import { Card, Statistic, Tooltip } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';

interface MetricCardProps {
  title: string;
  value: number | string;
  suffix?: string;
  prefix?: React.ReactNode;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: number;
  trendLabel?: string;
  color?: string;
  gradient?: string;
  loading?: boolean;
  tooltip?: string;
  onClick?: () => void;
}

/**
 * MetricCard - Componente para mostrar KPIs y métricas
 *
 * Uso:
 * <MetricCard
 *   title="Accidentes del Mes"
 *   value={0}
 *   icon={<SafetyCertificateOutlined />}
 *   color="#52c41a"
 *   trend="down"
 *   trendValue={100}
 *   trendLabel="vs mes anterior"
 * />
 */
export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  suffix,
  prefix,
  icon,
  trend,
  trendValue,
  trendLabel,
  color,
  gradient,
  loading = false,
  tooltip,
  onClick,
}) => {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <ArrowUpOutlined style={{ color: '#52c41a' }} />;
      case 'down':
        return <ArrowDownOutlined style={{ color: '#f5222d' }} />;
      default:
        return <MinusOutlined style={{ color: '#8c8c8c' }} />;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return '#52c41a';
      case 'down':
        return '#f5222d';
      default:
        return '#8c8c8c';
    }
  };

  const cardStyle: React.CSSProperties = {
    cursor: onClick ? 'pointer' : 'default',
    background: gradient || undefined,
    borderRadius: 8,
    transition: 'all 0.3s ease',
  };

  const content = (
    <Card
      style={cardStyle}
      hoverable={!!onClick}
      onClick={onClick}
      loading={loading}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ flex: 1 }}>
          <Statistic
            title={<span style={{ color: '#8c8c8c', fontSize: 14 }}>{title}</span>}
            value={value}
            suffix={suffix}
            prefix={prefix}
            valueStyle={{
              color: color || '#1890ff',
              fontSize: 28,
              fontWeight: 600,
            }}
          />
          {trend && trendValue !== undefined && (
            <div style={{ marginTop: 8, fontSize: 12 }}>
              {getTrendIcon()}
              <span style={{ color: getTrendColor(), marginLeft: 4 }}>
                {trendValue}%
              </span>
              {trendLabel && (
                <span style={{ color: '#8c8c8c', marginLeft: 4 }}>
                  {trendLabel}
                </span>
              )}
            </div>
          )}
        </div>
        {icon && (
          <div
            style={{
              fontSize: 32,
              color: color || '#1890ff',
              opacity: 0.8,
            }}
          >
            {icon}
          </div>
        )}
      </div>
    </Card>
  );

  if (tooltip) {
    return <Tooltip title={tooltip}>{content}</Tooltip>;
  }

  return content;
};
