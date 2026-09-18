import { useState, useEffect } from 'react';
import {
  Card, Table, Select, Space, Tag, Typography, Row, Col, Statistic,
  Progress, Avatar, Tabs, Badge, Tooltip, Button
} from 'antd';
import {
  UserOutlined, TrophyOutlined, CheckCircleOutlined, ClockCircleOutlined,
  TeamOutlined, BarChartOutlined, ExportOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { usersApi, planningApi, executionsApi } from '../../services/api';

const { Title, Text } = Typography;

interface TAEPerformance {
  id: number;
  full_name: string;
  email: string;
  employee_code: string;
  department_name: string;
  total_planned: number;
  total_executed: number;
  compliance_percentage: number;
  executions_approved: number;
  executions_pending: number;
  executions_rejected: number;
  rank: number;
}

const UsersPerformancePage = () => {
  const [loading, setLoading] = useState(true);
  const [performance, setPerformance] = useState<TAEPerformance[]>([]);
  const [year, setYear] = useState(dayjs().year());
  const [month, setMonth] = useState(dayjs().month() + 1);

  useEffect(() => {
    loadData();
  }, [year, month]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Cargar TAEs
      const taesResponse = await usersApi.getTAEs();

      // Cargar planes del mes
      const plansResponse = await planningApi.getPlans(year, month);

      // Calcular performance por TAE
      const performanceData: TAEPerformance[] = [];

      for (const tae of taesResponse) {
        const plan = plansResponse.find((p: any) => p.user_id === tae.id);

        // Obtener stats de ejecuciones
        let stats = { completed: 0, pending_approval: 0, approved: 0, rejected: 0 };
        try {
          stats = await executionsApi.getStats(year, month);
        } catch (e) {
          // Ignore error
        }

        performanceData.push({
          id: tae.id,
          full_name: tae.full_name,
          email: tae.email,
          employee_code: tae.employee_code || '',
          department_name: tae.department_name || 'Sin departamento',
          total_planned: plan?.total_planned || 0,
          total_executed: plan?.total_executed || 0,
          compliance_percentage: plan?.compliance_percentage || 0,
          executions_approved: stats.approved || 0,
          executions_pending: stats.pending_approval || 0,
          executions_rejected: stats.rejected || 0,
          rank: 0
        });
      }

      // Ordenar por cumplimiento y asignar rank
      performanceData.sort((a, b) => b.compliance_percentage - a.compliance_percentage);
      performanceData.forEach((p, i) => p.rank = i + 1);

      setPerformance(performanceData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getComplianceColor = (percentage: number) => {
    if (percentage >= 80) return '#52c41a';
    if (percentage >= 50) return '#faad14';
    return '#ff4d4f';
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) return <Badge count={<TrophyOutlined style={{ color: '#faad14' }} />} />;
    if (rank === 2) return <Badge count={<TrophyOutlined style={{ color: '#a0a0a0' }} />} />;
    if (rank === 3) return <Badge count={<TrophyOutlined style={{ color: '#cd7f32' }} />} />;
    return <span style={{ color: '#999' }}>#{rank}</span>;
  };

  const columns = [
    {
      title: '#',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      align: 'center' as const,
      render: (rank: number) => getRankBadge(rank),
    },
    {
      title: 'TAE',
      key: 'tae',
      render: (_: any, record: TAEPerformance) => (
        <Space>
          <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
          <div>
            <Text strong>{record.full_name}</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>{record.employee_code}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: 'Departamento',
      dataIndex: 'department_name',
      key: 'department',
      ellipsis: true,
    },
    {
      title: 'Plan',
      key: 'plan',
      width: 100,
      align: 'center' as const,
      render: (_: any, record: TAEPerformance) => (
        <Tooltip title={`${record.total_executed} ejecutadas de ${record.total_planned} planeadas`}>
          <span>{record.total_executed} / {record.total_planned}</span>
        </Tooltip>
      ),
    },
    {
      title: 'Cumplimiento',
      key: 'compliance',
      width: 180,
      render: (_: any, record: TAEPerformance) => (
        <div>
          <Progress
            percent={Math.round(record.compliance_percentage)}
            strokeColor={getComplianceColor(record.compliance_percentage)}
            size="small"
          />
        </div>
      ),
    },
    {
      title: 'Aprobadas',
      dataIndex: 'executions_approved',
      key: 'approved',
      width: 90,
      align: 'center' as const,
      render: (val: number) => <Tag color="green">{val}</Tag>,
    },
    {
      title: 'Pendientes',
      dataIndex: 'executions_pending',
      key: 'pending',
      width: 90,
      align: 'center' as const,
      render: (val: number) => val > 0 ? <Tag color="orange">{val}</Tag> : <Tag>{val}</Tag>,
    },
    {
      title: 'Rechazadas',
      dataIndex: 'executions_rejected',
      key: 'rejected',
      width: 90,
      align: 'center' as const,
      render: (val: number) => val > 0 ? <Tag color="red">{val}</Tag> : <Tag>{val}</Tag>,
    },
  ];

  const months = [
    { value: 1, label: 'Enero' }, { value: 2, label: 'Febrero' }, { value: 3, label: 'Marzo' },
    { value: 4, label: 'Abril' }, { value: 5, label: 'Mayo' }, { value: 6, label: 'Junio' },
    { value: 7, label: 'Julio' }, { value: 8, label: 'Agosto' }, { value: 9, label: 'Septiembre' },
    { value: 10, label: 'Octubre' }, { value: 11, label: 'Noviembre' }, { value: 12, label: 'Diciembre' },
  ];

  const totalTaes = performance.length;
  const avgCompliance = performance.length > 0
    ? performance.reduce((sum, p) => sum + p.compliance_percentage, 0) / performance.length
    : 0;
  const above80 = performance.filter(p => p.compliance_percentage >= 80).length;
  const below50 = performance.filter(p => p.compliance_percentage < 50).length;

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>
            <TeamOutlined style={{ marginRight: 8 }} />
            Desempeño de TAEs
          </Title>
          <Text type="secondary">Seguimiento del cumplimiento y rendimiento del equipo</Text>
        </div>
        <Space>
          <Select value={month} onChange={setMonth} options={months} style={{ width: 140 }} />
          <Select
            value={year}
            onChange={setYear}
            options={[{ value: 2024, label: '2024' }, { value: 2025, label: '2025' }, { value: 2026, label: '2026' }]}
            style={{ width: 100 }}
          />
          <Button icon={<ExportOutlined />}>Exportar</Button>
        </Space>
      </div>

      {/* KPIs */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Total TAEs"
              value={totalTaes}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Cumplimiento Promedio"
              value={avgCompliance.toFixed(1)}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: getComplianceColor(avgCompliance) }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Cumplimiento > 80%"
              value={above80}
              suffix={`/ ${totalTaes}`}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Cumplimiento < 50%"
              value={below50}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: below50 > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs
        defaultActiveKey="ranking"
        items={[
          {
            key: 'ranking',
            label: (
              <span>
                <TrophyOutlined />
                Ranking
              </span>
            ),
            children: (
              <Card>
                <Table
                  dataSource={performance}
                  columns={columns}
                  rowKey="id"
                  loading={loading}
                  pagination={false}
                  size="middle"
                />
              </Card>
            ),
          },
          {
            key: 'alerts',
            label: (
              <span>
                <ClockCircleOutlined />
                Alertas
                {below50 > 0 && <Badge count={below50} style={{ marginLeft: 8 }} />}
              </span>
            ),
            children: (
              <Card>
                <Table
                  dataSource={performance.filter(p => p.compliance_percentage < 50)}
                  columns={columns}
                  rowKey="id"
                  loading={loading}
                  pagination={false}
                  size="middle"
                  locale={{ emptyText: 'No hay TAEs con cumplimiento menor a 50%' }}
                />
              </Card>
            ),
          },
          {
            key: 'top',
            label: (
              <span>
                <TrophyOutlined style={{ color: '#faad14' }} />
                Top Performers
              </span>
            ),
            children: (
              <Card>
                <Table
                  dataSource={performance.filter(p => p.compliance_percentage >= 80)}
                  columns={columns}
                  rowKey="id"
                  loading={loading}
                  pagination={false}
                  size="middle"
                  locale={{ emptyText: 'No hay TAEs con cumplimiento mayor a 80%' }}
                />
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
};

export default UsersPerformancePage;
