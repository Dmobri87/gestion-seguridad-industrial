import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card, Table, InputNumber, Button, Space, Tag, Progress, Spin,
  Collapse, Typography, Descriptions, message, Popconfirm, Switch, Empty
} from 'antd';
import { ArrowLeftOutlined, SaveOutlined, CheckOutlined, DeleteOutlined, AppstoreAddOutlined } from '@ant-design/icons';
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
  const isAdmin = user?.role === 'Administrador';

  useEffect(() => {
    loadPlan();
  }, [planId]);

  const loadPlan = async () => {
    setLoading(true);
    try {
      const response = await planningApi.getPlan(Number(planId));
      setPlan(response);
      setActivities(response.planned_activities || []);
      // Cargar plantillas según si es plan propio del coordinador o plan de TAE
      await loadTemplatesForPlan(response);
    } catch (error: any) {
      console.error('Error loading plan:', error);
      const detail = error?.response?.data?.detail || 'Error al cargar el plan';
      message.error(detail);
      navigate('/planificacion');
    } finally {
      setLoading(false);
    }
  };

  const loadTemplatesForPlan = async (planData: any) => {
    try {
      // Si el coordinador está viendo su propio plan → plantillas de coordinador
      // Si está viendo un plan de TAE → plantillas normales
      const isCoordinatorOwnPlan = isCoordinator && planData.user_id === user?.id;
      const response = await activityApi.getTemplatesGrouped(isCoordinatorOwnPlan ? true : false);
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
            cycle_4_planned: 0,
            requires_evidence: true,
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

  const handleDeletePlan = async () => {
    try {
      await planningApi.deletePlan(Number(planId));
      message.success('Plan eliminado');
      navigate('/planificacion');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al eliminar el plan');
    }
  };

  const handleDeleteActivity = async (activityId: number) => {
    try {
      await planningApi.deleteActivity(activityId);
      message.success('Actividad eliminada');
      loadPlan();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al eliminar la actividad');
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
          {(record as any).coordinator_only && <Tag color="orange">Coordinador</Tag>}
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: 'Evidencia',
      key: 'requires_evidence',
      align: 'center' as const,
      width: 120,
      render: (_: any, record: PlannedActivity) => (
        <Switch
          checked={changes[record.id]?.requires_evidence ?? record.requires_evidence ?? true}
          onChange={(checked) => {
            setChanges((prev) => ({
              ...prev,
              [record.id]: {
                ...prev[record.id],
                requires_evidence: checked,
              },
            }));
          }}
          disabled={!isCoordinator || plan?.status !== 'Borrador'}
          checkedChildren="Sí"
          unCheckedChildren="No"
        />
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
      title: 'Total',
      key: 'total',
      align: 'center' as const,
      width: 80,
      render: (_: any, record: PlannedActivity) => {
        const planned = (changes[record.id]?.cycle_1_planned ?? record.cycle_1_planned) +
                       (changes[record.id]?.cycle_2_planned ?? record.cycle_2_planned) +
                       (changes[record.id]?.cycle_3_planned ?? record.cycle_3_planned);
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
    ...(isAdmin ? [{
      title: 'Acciones',
      key: 'actions',
      width: 110,
      render: (_: any, record: PlannedActivity) => (
        <Popconfirm
          title="Eliminar actividad"
          description="Se eliminará esta actividad del plan si no tiene ejecuciones. ¿Continuar?"
          onConfirm={() => handleDeleteActivity(record.id)}
          okText="Eliminar"
          cancelText="Cancelar"
        >
          <Button type="link" danger size="small" icon={<DeleteOutlined />}>
            Eliminar
          </Button>
        </Popconfirm>
      ),
    }] : []),
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!plan) {
    return null;
  }

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Space style={{ marginBottom: 16 }}>
              <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/planificacion')}>
                Volver
              </Button>
            </Space>

            <Descriptions column={3}>
              <Descriptions.Item label={plan.user_id === user?.id ? 'Coordinador' : 'TAE'}>{plan.user_name}</Descriptions.Item>
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
              {plan.status === 'Borrador' && (
                <Button icon={<AppstoreAddOutlined />} onClick={handleAddActivities}>
                  {activities.length === 0 ? 'Cargar Actividades' : 'Agregar Actividades'}
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
              {isAdmin && (
                <Popconfirm
                  title="Eliminar plan mensual"
                  description="Esta acción eliminará el plan completo si no tiene ejecuciones. ¿Continuar?"
                  onConfirm={handleDeletePlan}
                  okText="Eliminar"
                  cancelText="Cancelar"
                >
                  <Button danger icon={<DeleteOutlined />}>
                    Eliminar Plan
                  </Button>
                </Popconfirm>
              )}
            </Space>
          )}
        </div>
      </Card>

      {activities.length === 0 ? (
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <Space direction="vertical" size={4}>
                <span style={{ fontWeight: 500 }}>Este plan no tiene actividades programadas</span>
                <span style={{ color: '#8c8c8c', fontSize: 13 }}>
                  {isCoordinator
                    ? 'Usa "Agregar Actividades" para cargar las actividades del catálogo en este plan.'
                    : 'El coordinador aún no ha cargado las actividades para este plan. Consulta con tu supervisor.'}
                </span>
              </Space>
            }
          >
            {isCoordinator && plan.status === 'Borrador' && (
              <Button type="primary" icon={<AppstoreAddOutlined />} onClick={handleAddActivities}>
                Cargar Actividades del Catálogo
              </Button>
            )}
          </Empty>
        </Card>
      ) : (
        <Collapse>
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
                scroll={{ x: 500 }}
                pagination={false}
                size="small"
              />
            </Panel>
          ))}
        </Collapse>
      )}
    </div>
  );
};

export default PlanningDetailPage;
