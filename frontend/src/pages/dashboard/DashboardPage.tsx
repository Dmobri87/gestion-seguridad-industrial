import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Row, Col, Card, Progress, List, Tag, Spin, Select, Typography, Badge, Space, Alert } from 'antd';
import {
  SafetyOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  ToolOutlined,
  SafetyCertificateOutlined,
  WarningOutlined,
  ArrowRightOutlined,
  FireOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons';
import { Area } from '@ant-design/charts';
import dayjs from 'dayjs';
import { dashboardApi } from '../../services/api';

const { Title, Text } = Typography;

interface DashboardResponse {
  period: string;
  year: number;
  month: number;
  main_kpis: {
    accidents: { title: string; value: number; color: string };
    emergencies: { title: string; value: number; color: string };
    compliance: { title: string; value: number; unit: string; color: string };
    pending_activities: { title: string; value: number; color: string };
  };
  compliance: {
    overall_compliance: number;
    by_category: {
      category_id: number;
      category_name: string;
      category_code: string;
      category_color: string;
      total_planned: number;
      total_executed: number;
      compliance_percentage: number;
    }[];
    monthly_trend: {
      year: number;
      month: number;
      month_name: string;
      compliance_percentage: number;
    }[];
  };
  emergencies: {
    total: number;
    avg_response_time: number;
    this_month: number;
  };
  alerts: {
    total: number;
    critical: number;
    urgent: number;
    warning: number;
    alerts: {
      id: number;
      type: string;
      priority: string;
      title: string;
      description: string;
      due_date: string;
    }[];
  };
  top_performers: {
    top_performers: {
      user_id: number;
      user_name: string;
      compliance_percentage: number;
      total_executed: number;
      rank: number;
    }[];
  };
  equipment: {
    total: number;
    operational: number;
    in_maintenance: number;
    out_of_service: number;
    pending_maintenance: number;
  };
  certifications: {
    total_personal: number;
    expiring_30_days: number;
    expiring_15_days: number;
    expiring_7_days: number;
    expired: number;
  };
}

/* ─── Metric card con gradiente ─── */
const MetricCard = ({
  title, value, suffix, subtitle, icon, gradient, onClick, trend,
}: {
  title: string;
  value: number | string;
  suffix?: string;
  subtitle?: string;
  icon: React.ReactNode;
  gradient: string;
  onClick?: () => void;
  trend?: { direction: 'up' | 'down' | 'neutral'; label: string };
}) => (
  <div
    onClick={onClick}
    style={{
      background: gradient,
      borderRadius: 16,
      padding: '24px 20px',
      color: '#fff',
      cursor: onClick ? 'pointer' : 'default',
      transition: 'transform 0.2s, box-shadow 0.2s',
      boxShadow: '0 4px 15px rgba(0,0,0,0.08)',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      minHeight: 160,
    }}
    onMouseEnter={(e) => {
      if (onClick) {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)';
      }
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = '0 4px 15px rgba(0,0,0,0.08)';
    }}
  >
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div>
        <div style={{ fontSize: 13, opacity: 0.85, fontWeight: 500, marginBottom: 8 }}>{title}</div>
        <div style={{ fontSize: 36, fontWeight: 700, lineHeight: 1.1 }}>
          {value}
          {suffix && <span style={{ fontSize: 20, fontWeight: 500, marginLeft: 2 }}>{suffix}</span>}
        </div>
      </div>
      <div style={{
        background: 'rgba(255,255,255,0.2)',
        borderRadius: 12,
        width: 48,
        height: 48,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 22,
      }}>
        {icon}
      </div>
    </div>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 }}>
      {subtitle && <div style={{ fontSize: 12, opacity: 0.75 }}>{subtitle}</div>}
      {trend && (
        <div style={{
          fontSize: 12,
          background: 'rgba(255,255,255,0.2)',
          borderRadius: 20,
          padding: '2px 10px',
          display: 'flex',
          alignItems: 'center',
          gap: 4,
        }}>
          {trend.direction === 'up' && <RiseOutlined />}
          {trend.direction === 'down' && <FallOutlined />}
          {trend.label}
        </div>
      )}
    </div>
  </div>
);

/* ─── Dashboard Page ─── */
const DashboardPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [year, setYear] = useState(dayjs().year());
  const [month, setMonth] = useState(dayjs().month() + 1);

  const months = [
    { value: 1, label: 'Enero' }, { value: 2, label: 'Febrero' }, { value: 3, label: 'Marzo' },
    { value: 4, label: 'Abril' }, { value: 5, label: 'Mayo' }, { value: 6, label: 'Junio' },
    { value: 7, label: 'Julio' }, { value: 8, label: 'Agosto' }, { value: 9, label: 'Septiembre' },
    { value: 10, label: 'Octubre' }, { value: 11, label: 'Noviembre' }, { value: 12, label: 'Diciembre' },
  ];

  useEffect(() => {
    loadDashboard();
  }, [year, month]);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const response = await dashboardApi.getData(year, month);
      setData(response);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getComplianceColor = (pct: number) => {
    if (pct >= 80) return '#52c41a';
    if (pct >= 50) return '#faad14';
    return '#ff4d4f';
  };

  const getPriorityColor = (p: string) =>
    ({ critical: 'red', urgent: 'orange', warning: 'gold', info: 'blue' }[p] || 'default');

  const trendChartData = useMemo(() => {
    if (!data) return [];
    return data.compliance.monthly_trend.map((t) => ({
      month: `${t.month_name.substring(0, 3)} ${t.year}`,
      Cumplimiento: Number(t.compliance_percentage.toFixed(1)),
    }));
  }, [data]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!data) return <div>Error al cargar el dashboard</div>;

  const prevMonth = data.compliance.monthly_trend.length >= 2
    ? data.compliance.monthly_trend[data.compliance.monthly_trend.length - 2].compliance_percentage
    : 0;
  const complianceDelta = data.compliance.overall_compliance - prevMonth;

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      {/* ═══ Header ═══ */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <Title level={3} style={{ margin: 0, fontWeight: 700 }}>Panel de Gestión GAE</Title>
          <Text type="secondary">{data.period}</Text>
        </div>
        <Space>
          <Select value={month} onChange={setMonth} options={months} style={{ width: 140 }} />
          <Select
            value={year}
            onChange={setYear}
            options={[{ value: 2024, label: '2024' }, { value: 2025, label: '2025' }, { value: 2026, label: '2026' }]}
            style={{ width: 100 }}
          />
        </Space>
      </div>

      {/* ═══ Alertas ═══ */}
      {data.alerts.total > 0 && (
        <Alert
          message={
            <Space>
              <WarningOutlined />
              <span>Tienes <strong>{data.alerts.total}</strong> alertas activas</span>
              {data.alerts.critical > 0 && <Tag color="red">{data.alerts.critical} {'críticas'}</Tag>}
              {data.alerts.urgent > 0 && <Tag color="orange">{data.alerts.urgent} urgentes</Tag>}
            </Space>
          }
          type="warning"
          showIcon={false}
          style={{ marginBottom: 20, borderRadius: 12 }}
          action={<a onClick={() => navigate('/certifications')}>Ver detalles <ArrowRightOutlined /></a>}
        />
      )}

      {/* ═══ KPI Cards ═══ */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="Accidentes del Mes"
            value={data.main_kpis.accidents.value}
            icon={<SafetyOutlined />}
            gradient={data.main_kpis.accidents.value === 0
              ? 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
              : 'linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%)'}
            subtitle={data.main_kpis.accidents.value === 0 ? 'Sin accidentes' : 'Requiere atención'}
            trend={{ direction: 'neutral', label: data.main_kpis.accidents.value === 0 ? 'Objetivo cumplido' : 'Revisar' }}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="Emergencias Atendidas"
            value={data.main_kpis.emergencies.value}
            icon={<FireOutlined />}
            gradient="linear-gradient(135deg, #fa8c16 0%, #f5222d 100%)"
            subtitle={`Tiempo promedio: ${data.emergencies.avg_response_time?.toFixed(1) || 0} min`}
            onClick={() => navigate('/emergencies')}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="Cumplimiento General"
            value={data.compliance.overall_compliance.toFixed(1)}
            suffix="%"
            icon={<CheckCircleOutlined />}
            gradient={data.compliance.overall_compliance >= 80
              ? 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)'
              : data.compliance.overall_compliance >= 50
                ? 'linear-gradient(135deg, #faad14 0%, #d48806 100%)'
                : 'linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%)'}
            onClick={() => navigate('/planning')}
            trend={complianceDelta !== 0
              ? { direction: complianceDelta > 0 ? 'up' : 'down', label: `${complianceDelta > 0 ? '+' : ''}${complianceDelta.toFixed(1)}% vs mes ant.` }
              : undefined}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="Actividades Pendientes"
            value={data.main_kpis.pending_activities.value}
            icon={<ClockCircleOutlined />}
            gradient="linear-gradient(135deg, #722ed1 0%, #531dab 100%)"
            subtitle="Por ejecutar este mes"
            onClick={() => navigate('/execution')}
          />
        </Col>
      </Row>

      {/* ═══ Tendencia + Cumplimiento por Categoría ═══ */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={14}>
          <Card
            title={<Text strong style={{ fontSize: 15 }}>Tendencia de Cumplimiento</Text>}
            extra={<Text type="secondary" style={{ fontSize: 12 }}>Últimos 6 meses</Text>}
            styles={{ body: { padding: '12px 16px 0' } }}
            style={{ borderRadius: 12, height: '100%' }}
          >
            <Area
              data={trendChartData}
              xField="month"
              yField="Cumplimiento"
              shapeField="smooth"
              height={260}
              style={{ fill: 'linear-gradient(-90deg, rgba(24,144,255,0.25) 0%, rgba(24,144,255,0.02) 100%)' }}
              line={{ style: { stroke: '#1890ff', lineWidth: 3 }, shapeField: 'smooth' }}
              point={{ style: { fill: '#1890ff', stroke: '#fff', lineWidth: 2, r: 4 }, shapeField: 'point' }}
              axis={{ y: { labelFormatter: (v: number) => `${v}%` } }}
              scale={{ y: { domainMin: 0, domainMax: 100 } }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card
            title={<Text strong style={{ fontSize: 15 }}>Cumplimiento por Categoría</Text>}
            extra={<a onClick={() => navigate('/activities')} style={{ fontSize: 12 }}>Ver catálogo <ArrowRightOutlined /></a>}
            styles={{ body: { padding: '12px 20px' } }}
            style={{ borderRadius: 12, height: '100%' }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {data.compliance.by_category.map((cat) => (
                <div key={cat.category_id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <Space size={8}>
                      <div style={{ width: 10, height: 10, borderRadius: 3, background: cat.category_color }} />
                      <Text style={{ fontSize: 13 }}>{cat.category_name}</Text>
                    </Space>
                    <Space size={12}>
                      <Text type="secondary" style={{ fontSize: 12 }}>{cat.total_executed}/{cat.total_planned}</Text>
                      <Text strong style={{ fontSize: 13, color: getComplianceColor(cat.compliance_percentage), minWidth: 45, textAlign: 'right' }}>
                        {cat.compliance_percentage.toFixed(1)}%
                      </Text>
                    </Space>
                  </div>
                  <Progress
                    percent={cat.compliance_percentage}
                    strokeColor={cat.category_color}
                    trailColor="#f0f0f0"
                    showInfo={false}
                    size="small"
                  />
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {/* ═══ Top Performers + Equipos & Certificaciones ═══ */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={8}>
          <Card
            title={
              <Space>
                <TrophyOutlined style={{ color: '#faad14' }} />
                <Text strong style={{ fontSize: 15 }}>Top Performers</Text>
              </Space>
            }
            styles={{ body: { padding: '8px 16px' } }}
            style={{ borderRadius: 12, height: '100%' }}
          >
            <List
              size="small"
              dataSource={data.top_performers.top_performers.slice(0, 5)}
              renderItem={(item, idx) => (
                <List.Item style={{ padding: '10px 0', borderBottom: idx < 4 ? '1px solid #f5f5f5' : 'none' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1 }}>
                    <div style={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: 13,
                      color: idx <= 2 ? '#fff' : '#666',
                      background: idx === 0 ? 'linear-gradient(135deg, #faad14, #d48806)'
                        : idx === 1 ? 'linear-gradient(135deg, #a0a0a0, #808080)'
                          : idx === 2 ? 'linear-gradient(135deg, #cd7f32, #a0522d)'
                            : '#e8e8e8',
                    }}>
                      {item.rank}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <Text strong style={{ fontSize: 13, display: 'block' }} ellipsis>{item.user_name}</Text>
                      <Text type="secondary" style={{ fontSize: 11 }}>{item.total_executed} ejecuciones</Text>
                    </div>
                    <div style={{
                      background: getComplianceColor(item.compliance_percentage) + '18',
                      color: getComplianceColor(item.compliance_percentage),
                      borderRadius: 8,
                      padding: '4px 10px',
                      fontWeight: 700,
                      fontSize: 13,
                    }}>
                      {item.compliance_percentage.toFixed(1)}%
                    </div>
                  </div>
                </List.Item>
              )}
              locale={{ emptyText: 'Sin datos' }}
            />
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Row gutter={[16, 16]} style={{ height: '100%' }}>
            <Col xs={24} sm={12}>
              <Card
                hoverable
                onClick={() => navigate('/equipment')}
                style={{ borderRadius: 12, cursor: 'pointer', height: '100%' }}
                styles={{ body: { padding: 20 } }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                  <div style={{
                    width: 44, height: 44, borderRadius: 12,
                    background: 'linear-gradient(135deg, #1890ff22, #1890ff08)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <ToolOutlined style={{ fontSize: 20, color: '#1890ff' }} />
                  </div>
                  <div>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>Equipos Operativos</Text>
                    <Text strong style={{ fontSize: 28, lineHeight: 1.1 }}>
                      {data.equipment.operational}
                      <span style={{ fontSize: 16, color: '#999', fontWeight: 400 }}> / {data.equipment.total}</span>
                    </Text>
                  </div>
                </div>
                <Row gutter={8}>
                  {[
                    { label: 'En Mtto', value: data.equipment.in_maintenance, color: '#faad14' },
                    { label: 'Fuera Serv.', value: data.equipment.out_of_service, color: '#ff4d4f' },
                    { label: 'Pend. Mtto', value: data.equipment.pending_maintenance, color: '#722ed1' },
                  ].map((s) => (
                    <Col span={8} key={s.label}>
                      <div style={{ textAlign: 'center', padding: '8px 0', background: '#fafafa', borderRadius: 8 }}>
                        <div style={{ fontSize: 18, fontWeight: 700, color: s.color }}>{s.value}</div>
                        <div style={{ fontSize: 10, color: '#999' }}>{s.label}</div>
                      </div>
                    </Col>
                  ))}
                </Row>
              </Card>
            </Col>

            <Col xs={24} sm={12}>
              <Card
                hoverable
                onClick={() => navigate('/certifications')}
                style={{ borderRadius: 12, cursor: 'pointer', height: '100%' }}
                styles={{ body: { padding: 20 } }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                  <div style={{
                    width: 44, height: 44, borderRadius: 12,
                    background: 'linear-gradient(135deg, #52c41a22, #52c41a08)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <SafetyCertificateOutlined style={{ fontSize: 20, color: '#52c41a' }} />
                  </div>
                  <div>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>Certificaciones</Text>
                    <Text strong style={{ fontSize: 28, lineHeight: 1.1 }}>{data.certifications.total_personal}</Text>
                  </div>
                </div>
                <Row gutter={8}>
                  {[
                    { label: 'Vencidas', value: data.certifications.expired, color: '#ff4d4f' },
                    { label: '< 7 días', value: data.certifications.expiring_7_days, color: '#fa8c16' },
                    { label: '< 30 días', value: data.certifications.expiring_30_days, color: '#faad14' },
                  ].map((s) => (
                    <Col span={8} key={s.label}>
                      <div style={{ textAlign: 'center', padding: '8px 0', background: '#fafafa', borderRadius: 8 }}>
                        <div style={{ fontSize: 18, fontWeight: 700, color: s.value > 0 ? s.color : '#52c41a' }}>{s.value}</div>
                        <div style={{ fontSize: 10, color: '#999' }}>{s.label}</div>
                      </div>
                    </Col>
                  ))}
                </Row>
              </Card>
            </Col>
          </Row>
        </Col>
      </Row>

      {/* ═══ Alertas detalladas ═══ */}
      {data.alerts.alerts.length > 0 && (
        <Card
          title={
            <Space>
              <WarningOutlined style={{ color: '#faad14' }} />
              <Text strong style={{ fontSize: 15 }}>Alertas Recientes</Text>
              <Badge count={data.alerts.total} style={{ backgroundColor: '#faad14' }} />
            </Space>
          }
          style={{ borderRadius: 12 }}
          styles={{ body: { padding: '8px 16px' } }}
        >
          <List
            size="small"
            dataSource={data.alerts.alerts.slice(0, 5)}
            renderItem={(alert) => (
              <List.Item
                actions={[
                  <Text type="secondary" key="date" style={{ fontSize: 12 }}>
                    {dayjs(alert.due_date).format('DD/MM/YYYY')}
                  </Text>,
                ]}
                style={{ padding: '10px 0' }}
              >
                <List.Item.Meta
                  avatar={<Tag color={getPriorityColor(alert.priority)} style={{ borderRadius: 6 }}>{alert.priority.toUpperCase()}</Tag>}
                  title={<Text style={{ fontSize: 13 }}>{alert.title}</Text>}
                  description={<Text type="secondary" style={{ fontSize: 12 }}>{alert.description}</Text>}
                />
              </List.Item>
            )}
          />
        </Card>
      )}
    </div>
  );
};

export default DashboardPage;
