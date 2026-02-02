import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card, Table, InputNumber, Button, Space, Tag, Progress, Spin,
  Collapse, Typography, Descriptions, message, Popconfirm
} from 'antd';
import { ArrowLeftOutlined, SaveOutlined, CheckOutlined } from '@ant-design/icons';
import { planningApi, activityApi } from '../../services/api';
import type { PlannedActivity, ActivityCategory } from '../../types';
import { useAuthStore } from '../../stores/authStore';

const { Text } = Typography;
const { Panel } = Collapse;

interface GroupedActivities {
  [categoryCode: string]: {
    category: ActivityCategory;
    activities: PlannedActivity[];
  };
}

const PlanningDetailPage = () => {
  const { planId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [plan, setPlan] = useState<any>(null);
  const [templates, setTemplates] = useState<any>({});
  const [activities, setActivities] = useState<PlannedActivity[]>([]);
  const [changes, setChanges] = useState<Record<number, Partial<PlannedActivity>>>({});
  const user = useAuthStore((state) => state.user);

  const isCoordinator = ['Administrador', 'Coordinador'].includes(user?.role || '');

  useEffect(() => {
    loadPlan();
    loadTemplates();
  }, [planId]);

  const loadPlan = async () => {
    setLoading(true);
    try {
      const response = await planningApi.getPlan(Number(planId));
      setPlan(response);
      setActivities(response.planned_activities || []);
    } catch (error) {
      console.error('Error loading plan:', error);
      message.error('Error al cargar el plan');
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await activityApi.getTemplatesGrouped();
      setTemplates(response);
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  };

  const handleCycleChange = (activityId: number, cycle: number, value: number | null) => {
    setChanges((prev) => ({
      ...prev,
      [activityId]: {
        ...prev[activityId],
        [`cycle_${cycle}_planned`]: value || 0,
      },
    }));
  };

  const handleSave = async () => {
    if (Object.keys(changes).length === 0) {
      message.info('No hay cambios para guardar');
      return;
    }

    setSaving(true);
    try {
      for (const [activityId, data] of Object.entries(changes)) {
        await planningApi.updateActivity(Number(activityId), data);
      }
      message.success('Cambios guardados');
      setChanges({});
      loadPlan();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const handleAddActivities = async () => {
    // Agregar todas las actividades de las plantillas al plan
    const activitiesToAdd: any[] = [];

    Object.values(templates).forEach((cat: any) => {
      cat.templates.forEach((tmpl: any) => {
        // Verificar si ya existe
        const exists = activities.some((a) => a.activity_template_id === tmpl.id);
        if (!exists) {
          activitiesToAdd.push({
            activity_template_id: tmpl.id,
            cycle_1_planned: tmpl.default_frequency,
            cycle_2_planned: tmpl.default_frequency,
            cycle_3_planned: tmpl.default_frequency,
            cycle_4_planned: tmpl.default_frequency,
          });
        }
      });
    });

    if (activitiesToAdd.length === 0) {
      message.info('Todas las actividades ya están en el plan');
      return;
    }

    try {
      await planningApi.bulkAddActivities(Number(planId), activitiesToAdd);
      message.success(`${activitiesToAdd.length} actividades agregadas`);
      loadPlan();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al agregar actividades');
    }
  };

  const handleApprovePlan = async () => {
    try {
      await planningApi.approvePlan(Number(planId));
      message.success('Plan aprobado');
      loadPlan();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al aprobar el plan');
    }
  };

  const getComplianceColor = (percentage: number) => {
    if (percentage >= 80) return '#52c41a';
    if (percentage >= 50) return '#faad14';
    return '#ff4d4f';
  };

  const groupedActivities: GroupedActivities = activities.reduce((acc, activity) => {
    const code = activity.category_name || 'SIN_CATEGORIA';
    if (!acc[code]) {
      acc[code] = {
        category: {
          id: activity.category_id || 0,
          name: activity.category_name || 'Sin Categoría',
          code: code,
          color: '#1890ff',
          display_order: 0,
        },
        activities: [],
      };
    }
    acc[code].activities.push(activity);
    return acc;
  }, {} as GroupedActivities);

  const columns = [
    {
      title: 'Actividad',
      dataIndex: 'activity_name',
      key: 'activity_name',
      width: 300,
      render: (text: string, record: PlannedActivity) => (
        <Space>
          {record.is_critical && <Tag color="red">Crítica</Tag>}
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: 'Ciclo 1',
      key: 'cycle_1',
      align: 'center' as const,
      width: 100,
      render: (_: any, record: PlannedActivity) => (
        <Space direction="vertical" size={0}>
          <InputNumber
            size="small"
            min={0}
            max={99}
            value={changes[record.id]?.cycle_1_planned ?? record.cycle_1_planned}
            onChange={(v) => handleCycleChange(record.id, 1, v)}
            disabled={!isCoordinator || plan?.status !== 'Borrador'}
            style={{ width: 60 }}
          />
          <Text type="secondary" style={{ fontSize: 11 }}>
            Ej: {record.cycle_1_executed}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Ciclo 2',
      key: 'cycle_2',
      align: 'center' as const,
      width: 100,
      render: (_: any, record: PlannedActivity) => (
        <Space direction="vertical" size={0}>
          <InputNumber
            size="small"
            min={0}
            max={99}
            value={changes[record.id]?.cycle_2_planned ?? record.cycle_2_planned}
            onChange={(v) => handleCycleChange(record.id, 2, v)}
            disabled={!isCoordinator || plan?.status !== 'Borrador'}
            style={{ width: 60 }}
          />
          <Text type="secondary" style={{ fontSize: 11 }}>
            Ej: {record.cycle_2_executed}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Ciclo 3',
      key: 'cycle_3',
      align: 'center' as const,
      width: 100,
      render: (_: any, record: PlannedActivity) => (
        <Space direction="vertical" size={0}>
          <InputNumber
            size="small"
            min={0}
            max={99}
            value={changes[record.id]?.cycle_3_planned ?? record.cycle_3_planned}
            onChange={(v) => handleCycleChange(record.id, 3, v)}
            disabled={!isCoordinator || plan?.status !== 'Borrador'}
            style={{ width: 60 }}
          />
          <Text type="secondary" style={{ fontSize: 11 }}>
            Ej: {record.cycle_3_executed}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Ciclo 4',
      key: 'cycle_4',
      align: 'center' as const,
      width: 100,
      render: (_: any, record: PlannedActivity) => (
        <Space direction="vertical" size={0}>
          <InputNumber
            size="small"
            min={0}
            max={99}
            value={changes[record.id]?.cycle_4_planned ?? record.cycle_4_planned}
            onChange={(v) => handleCycleChange(record.id, 4, v)}
            disabled={!isCoordinator || plan?.status !== 'Borrador'}
            style={{ width: 60 }}
          />
          <Text type="secondary" style={{ fontSize: 11 }}>
            Ej: {record.cycle_4_executed}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Total',
      key: 'total',
      align: 'center' as const,
      width: 80,
      render: (_: any, record: PlannedActivity) => {
        const planned = (changes[record.id]?.cycle_1_planned ?? record.cycle_1_planned) +
                       (changes[record.id]?.cycle_2_planned ?? record.cycle_2_planned) +
                       (changes[record.id]?.cycle_3_planned ?? record.cycle_3_planned) +
                       (changes[record.id]?.cycle_4_planned ?? record.cycle_4_planned);
        return (
          <div>
            <div>{planned}</div>
            <Text type="secondary" style={{ fontSize: 11 }}>
              Ej: {record.total_executed}
            </Text>
          </div>
        );
      },
    },
    {
      title: '%',
      dataIndex: 'compliance_percentage',
      key: 'compliance',
      align: 'center' as const,
      width: 80,
      render: (value: number) => (
        <Progress
          type="circle"
          percent={Number(value.toFixed(0))}
          size={40}
          strokeColor={getComplianceColor(value)}
        />
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!plan) {
    return <div>Plan no encontrado</div>;
  }

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Space style={{ marginBottom: 16 }}>
              <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/planning')}>
                Volver
              </Button>
            </Space>

            <Descriptions column={3}>
              <Descriptions.Item label="TAE">{plan.user_name}</Descriptions.Item>
              <Descriptions.Item label="Período">
                {plan.month}/{plan.year}
              </Descriptions.Item>
              <Descriptions.Item label="Estado">
                <Tag color={plan.status === 'Aprobado' ? 'green' : 'default'}>{plan.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Total Planeado">{plan.total_planned}</Descriptions.Item>
              <Descriptions.Item label="Total Ejecutado">{plan.total_executed}</Descriptions.Item>
              <Descriptions.Item label="Cumplimiento">
                <Progress
                  percent={Number(plan.compliance_percentage.toFixed(0))}
                  size="small"
                  strokeColor={getComplianceColor(plan.compliance_percentage)}
                  style={{ width: 150 }}
                />
              </Descriptions.Item>
            </Descriptions>
          </div>

          {isCoordinator && (
            <Space>
              {plan.status === 'Borrador' && activities.length === 0 && (
                <Button onClick={handleAddActivities}>
                  Cargar Actividades
                </Button>
              )}
              {Object.keys(changes).length > 0 && (
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={handleSave}
                  loading={saving}
                >
                  Guardar Cambios
                </Button>
              )}
              {plan.status === 'Borrador' && plan.total_planned > 0 && (
                <Popconfirm
                  title="Aprobar Plan"
                  description="Una vez aprobado, no se podrá modificar. ¿Continuar?"
                  onConfirm={handleApprovePlan}
                  okText="Aprobar"
                  cancelText="Cancelar"
                >
                  <Button type="primary" icon={<CheckOutlined />}>
                    Aprobar Plan
                  </Button>
                </Popconfirm>
              )}
            </Space>
          )}
        </div>
      </Card>

      <Collapse defaultActiveKey={Object.keys(groupedActivities)}>
        {Object.entries(groupedActivities).map(([code, group]) => (
          <Panel
            header={
              <Space>
                <span style={{ fontWeight: 600 }}>{group.category.name}</span>
                <Tag>{group.activities.length} actividades</Tag>
              </Space>
            }
            key={code}
          >
            <Table
              dataSource={group.activities}
              columns={columns}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Panel>
        ))}
      </Collapse>
    </div>
  );
};

export default PlanningDetailPage;
