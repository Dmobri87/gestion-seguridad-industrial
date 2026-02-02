import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table, Button, Card, Select, Space, Tag, Progress, Modal,
  message, Typography, Checkbox, Row, Col, Divider, Alert, Switch
} from 'antd';
import { PlusOutlined, EyeOutlined, CheckOutlined, TeamOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { planningApi, usersApi, workGroupsApi } from '../../services/api';
import type { MonthlyPlan, User } from '../../types';
import { useAuthStore } from '../../stores/authStore';

const { Title, Text } = Typography;

const MONTHS = [
  { value: 1, label: 'Enero' },
  { value: 2, label: 'Febrero' },
  { value: 3, label: 'Marzo' },
  { value: 4, label: 'Abril' },
  { value: 5, label: 'Mayo' },
  { value: 6, label: 'Junio' },
  { value: 7, label: 'Julio' },
  { value: 8, label: 'Agosto' },
  { value: 9, label: 'Septiembre' },
  { value: 10, label: 'Octubre' },
  { value: 11, label: 'Noviembre' },
  { value: 12, label: 'Diciembre' },
];

const QUARTERS = [
  { label: 'Q1 (Ene - Mar)', months: [1, 2, 3] },
  { label: 'Q2 (Abr - Jun)', months: [4, 5, 6] },
  { label: 'Q3 (Jul - Sep)', months: [7, 8, 9] },
  { label: 'Q4 (Oct - Dic)', months: [10, 11, 12] },
];

const PlanningListPage = () => {
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [plans, setPlans] = useState<MonthlyPlan[]>([]);
  const [assignableUsers, setAssignableUsers] = useState<User[]>([]);
  const [workGroups, setWorkGroups] = useState<any[]>([]);
  const [year, setYear] = useState(dayjs().year());
  const [month, setMonth] = useState<number | undefined>(dayjs().month() + 1);
  const [modalOpen, setModalOpen] = useState(false);

  // Estado del formulario de creación masiva
  const [selectedYear, setSelectedYear] = useState(dayjs().year());
  const [selectedMonths, setSelectedMonths] = useState<number[]>([]);
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([]);
  const [loadActivities, setLoadActivities] = useState(true);

  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const isCoordinator = ['Administrador', 'Coordinador'].includes(user?.role || '');

  useEffect(() => {
    loadPlans();
    if (isCoordinator) {
      loadAssignableUsers();
      loadWorkGroups();
    }
  }, [year, month]);

  const loadPlans = async () => {
    setLoading(true);
    try {
      const response = await planningApi.getPlans(year, month);
      setPlans(response);
    } catch (error) {
      console.error('Error loading plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAssignableUsers = async () => {
    try {
      const response = await usersApi.getAssignable();
      setAssignableUsers(response);
    } catch (error) {
      console.error('Error loading assignable users:', error);
    }
  };

  const loadWorkGroups = async () => {
    try {
      const response = await workGroupsApi.getAll();
      setWorkGroups(response);
    } catch (error) {
      console.error('Error loading work groups:', error);
    }
  };

  // ==========================================
  // SELECCIÓN RÁPIDA DE MESES
  // ==========================================

  const handleQuarterSelect = (quarterMonths: number[]) => {
    const allSelected = quarterMonths.every((m) => selectedMonths.includes(m));
    if (allSelected) {
      setSelectedMonths(selectedMonths.filter((m) => !quarterMonths.includes(m)));
    } else {
      const merged = [...new Set([...selectedMonths, ...quarterMonths])];
      setSelectedMonths(merged.sort((a, b) => a - b));
    }
  };

  const handleMonthToggle = (monthValue: number) => {
    if (selectedMonths.includes(monthValue)) {
      setSelectedMonths(selectedMonths.filter((m) => m !== monthValue));
    } else {
      setSelectedMonths([...selectedMonths, monthValue].sort((a, b) => a - b));
    }
  };

  // ==========================================
  // SELECCIÓN RÁPIDA DE PERSONAL
  // ==========================================

  const handleSelectAllUsers = () => {
    if (selectedUserIds.length === assignableUsers.length) {
      setSelectedUserIds([]);
    } else {
      setSelectedUserIds(assignableUsers.map((u) => u.id));
    }
  };

  const handleSelectByRole = (role: string) => {
    const roleUsers = assignableUsers.filter((u) => u.role === role);
    const roleIds = roleUsers.map((u) => u.id);
    const allSelected = roleIds.every((id) => selectedUserIds.includes(id));
    if (allSelected) {
      setSelectedUserIds(selectedUserIds.filter((id) => !roleIds.includes(id)));
    } else {
      setSelectedUserIds([...new Set([...selectedUserIds, ...roleIds])]);
    }
  };

  const handleSelectByGroup = (groupId: number) => {
    const groupMembers = assignableUsers.filter((u: any) => u.work_group_id === groupId);
    const memberIds = groupMembers.map((u) => u.id);
    const allSelected = memberIds.every((id) => selectedUserIds.includes(id));
    if (allSelected) {
      setSelectedUserIds(selectedUserIds.filter((id) => !memberIds.includes(id)));
    } else {
      setSelectedUserIds([...new Set([...selectedUserIds, ...memberIds])]);
    }
  };

  // ==========================================
  // CREACIÓN MASIVA
  // ==========================================

  const handleBulkCreate = async () => {
    if (selectedMonths.length === 0) {
      message.warning('Selecciona al menos un mes');
      return;
    }
    if (selectedUserIds.length === 0) {
      message.warning('Selecciona al menos un usuario');
      return;
    }

    setCreating(true);
    try {
      const result = await planningApi.bulkCreatePlans({
        user_ids: selectedUserIds,
        months: selectedMonths.map((m) => ({ year: selectedYear, month: m })),
        organization_id: user?.organization_id,
        load_activities: loadActivities,
      });

      if (result.created > 0) {
        message.success(`${result.created} planes creados correctamente`);
      }
      if (result.skipped > 0) {
        message.info(`${result.skipped} planes omitidos (ya existentes)`);
      }

      setModalOpen(false);
      resetModalForm();
      loadPlans();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al crear los planes');
    } finally {
      setCreating(false);
    }
  };

  const resetModalForm = () => {
    setSelectedMonths([]);
    setSelectedUserIds([]);
    setLoadActivities(true);
    setSelectedYear(dayjs().year());
  };

  const handleApprovePlan = async (planId: number) => {
    try {
      await planningApi.approvePlan(planId);
      message.success('Plan aprobado');
      loadPlans();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al aprobar el plan');
    }
  };

  // ==========================================
  // RENDER HELPERS
  // ==========================================

  const getStatusTag = (status: string) => {
    const colors: Record<string, string> = {
      Borrador: 'default',
      Aprobado: 'green',
      'En Progreso': 'blue',
      Completado: 'purple',
      Cancelado: 'red',
    };
    return <Tag color={colors[status] || 'default'}>{status}</Tag>;
  };

  const getComplianceColor = (percentage: number) => {
    if (percentage >= 80) return '#52c41a';
    if (percentage >= 50) return '#faad14';
    return '#ff4d4f';
  };

  const totalPlansToCreate = selectedMonths.length * selectedUserIds.length;

  const columns = [
    {
      title: 'Personal',
      dataIndex: 'user_name',
      key: 'user_name',
    },
    {
      title: 'Período',
      key: 'period',
      render: (_: any, record: MonthlyPlan) => (
        <span>{MONTHS.find((m) => m.value === record.month)?.label} {record.year}</span>
      ),
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
    },
    {
      title: 'Planeado',
      dataIndex: 'total_planned',
      key: 'total_planned',
      align: 'center' as const,
    },
    {
      title: 'Ejecutado',
      dataIndex: 'total_executed',
      key: 'total_executed',
      align: 'center' as const,
    },
    {
      title: 'Cumplimiento',
      dataIndex: 'compliance_percentage',
      key: 'compliance_percentage',
      render: (value: number) => (
        <Progress
          percent={Number(value.toFixed(0))}
          size="small"
          strokeColor={getComplianceColor(value)}
        />
      ),
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_: any, record: MonthlyPlan) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/planning/${record.id}`)}
          >
            Ver
          </Button>
          {isCoordinator && record.status === 'Borrador' && (
            <Button
              type="link"
              icon={<CheckOutlined />}
              onClick={() => handleApprovePlan(record.id)}
            >
              Aprobar
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>Planes Mensuales</Title>

          <Space>
            <Select
              value={month}
              onChange={setMonth}
              allowClear
              placeholder="Todos los meses"
              options={MONTHS}
              style={{ width: 160 }}
            />
            <Select
              value={year}
              onChange={setYear}
              options={[
                { value: 2024, label: '2024' },
                { value: 2025, label: '2025' },
                { value: 2026, label: '2026' },
                { value: 2027, label: '2027' },
              ]}
              style={{ width: 100 }}
            />
            {isCoordinator && (
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setSelectedYear(year);
                  setModalOpen(true);
                }}
              >
                Programar Planes
              </Button>
            )}
          </Space>
        </div>

        <Table
          dataSource={plans}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 15 }}
        />
      </Card>

      {/* ==========================================
          MODAL DE CREACIÓN MASIVA
          ========================================== */}
      <Modal
        title={
          <Space>
            <TeamOutlined />
            <span>Programar Planes Mensuales</span>
          </Space>
        }
        open={modalOpen}
        onCancel={() => { setModalOpen(false); resetModalForm(); }}
        onOk={handleBulkCreate}
        okText={`Crear ${totalPlansToCreate} plan${totalPlansToCreate !== 1 ? 'es' : ''}`}
        okButtonProps={{ disabled: totalPlansToCreate === 0, loading: creating }}
        cancelText="Cancelar"
        width={700}
      >
        {/* ---- SECCIÓN: AÑO ---- */}
        <div style={{ marginBottom: 16 }}>
          <Text strong>Año</Text>
          <div style={{ marginTop: 8 }}>
            <Select
              value={selectedYear}
              onChange={setSelectedYear}
              options={[
                { value: 2025, label: '2025' },
                { value: 2026, label: '2026' },
                { value: 2027, label: '2027' },
              ]}
              style={{ width: 120 }}
            />
          </div>
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* ---- SECCIÓN: MESES ---- */}
        <div style={{ marginBottom: 16 }}>
          <Text strong>Meses</Text>
          <div style={{ marginTop: 8, marginBottom: 8 }}>
            <Space wrap>
              {QUARTERS.map((q) => {
                const allSelected = q.months.every((m) => selectedMonths.includes(m));
                return (
                  <Button
                    key={q.label}
                    size="small"
                    type={allSelected ? 'primary' : 'default'}
                    onClick={() => handleQuarterSelect(q.months)}
                  >
                    {q.label}
                  </Button>
                );
              })}
            </Space>
          </div>
          <Row gutter={[8, 8]}>
            {MONTHS.map((m) => (
              <Col span={6} key={m.value}>
                <Checkbox
                  checked={selectedMonths.includes(m.value)}
                  onChange={() => handleMonthToggle(m.value)}
                >
                  {m.label}
                </Checkbox>
              </Col>
            ))}
          </Row>
          {selectedMonths.length > 0 && (
            <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
              {selectedMonths.length} mes{selectedMonths.length > 1 ? 'es' : ''} seleccionado{selectedMonths.length > 1 ? 's' : ''}
            </Text>
          )}
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* ---- SECCIÓN: PERSONAL ---- */}
        <div style={{ marginBottom: 16 }}>
          <Text strong>Personal</Text>
          <div style={{ marginTop: 8, marginBottom: 8 }}>
            <Space wrap>
              <Button
                size="small"
                type={selectedUserIds.length === assignableUsers.length && assignableUsers.length > 0 ? 'primary' : 'default'}
                onClick={handleSelectAllUsers}
              >
                Todos
              </Button>
              <Button
                size="small"
                type={
                  assignableUsers.filter((u) => u.role === 'TAE').length > 0 &&
                  assignableUsers.filter((u) => u.role === 'TAE').every((u) => selectedUserIds.includes(u.id))
                    ? 'primary' : 'default'
                }
                onClick={() => handleSelectByRole('TAE')}
              >
                TAEs
              </Button>
              <Button
                size="small"
                type={
                  assignableUsers.filter((u) => u.role === 'PSE').length > 0 &&
                  assignableUsers.filter((u) => u.role === 'PSE').every((u) => selectedUserIds.includes(u.id))
                    ? 'primary' : 'default'
                }
                onClick={() => handleSelectByRole('PSE')}
              >
                PSEs
              </Button>
              <Button
                size="small"
                type={
                  assignableUsers.filter((u) => u.role === 'Supervisor').length > 0 &&
                  assignableUsers.filter((u) => u.role === 'Supervisor').every((u) => selectedUserIds.includes(u.id))
                    ? 'primary' : 'default'
                }
                onClick={() => handleSelectByRole('Supervisor')}
              >
                Supervisores
              </Button>
            </Space>
          </div>

          {/* Botones por grupo de trabajo */}
          {workGroups.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>Por grupo:</Text>
              <div style={{ marginTop: 4 }}>
                <Space wrap>
                  {workGroups.map((g: any) => (
                    <Button
                      key={g.id}
                      size="small"
                      type={
                        assignableUsers.filter((u: any) => u.work_group_id === g.id).length > 0 &&
                        assignableUsers.filter((u: any) => u.work_group_id === g.id).every((u) => selectedUserIds.includes(u.id))
                          ? 'primary' : 'default'
                      }
                      onClick={() => handleSelectByGroup(g.id)}
                    >
                      {g.name}
                    </Button>
                  ))}
                </Space>
              </div>
            </div>
          )}

          <Select
            mode="multiple"
            placeholder="Selecciona personal"
            value={selectedUserIds}
            onChange={setSelectedUserIds}
            style={{ width: '100%', marginTop: 8 }}
            maxTagCount={5}
            maxTagPlaceholder={(omitted) => `+${omitted.length} más`}
            options={assignableUsers.map((u) => ({
              value: u.id,
              label: `${u.full_name} (${u.role})`,
            }))}
            filterOption={(input, option) =>
              (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
            }
          />
          {selectedUserIds.length > 0 && (
            <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
              {selectedUserIds.length} persona{selectedUserIds.length > 1 ? 's' : ''} seleccionada{selectedUserIds.length > 1 ? 's' : ''}
            </Text>
          )}
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* ---- SECCIÓN: OPCIONES ---- */}
        <div style={{ marginBottom: 8 }}>
          <Space>
            <Switch
              checked={loadActivities}
              onChange={setLoadActivities}
              size="small"
            />
            <Text>Cargar actividades del catálogo automáticamente</Text>
          </Space>
          <div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Si se activa, cada plan se creará con todas las actividades del catálogo ya asignadas.
            </Text>
          </div>
        </div>

        {/* ---- RESUMEN ---- */}
        {totalPlansToCreate > 0 && (
          <Alert
            type="info"
            showIcon
            message={
              <span>
                Se crearán <strong>{totalPlansToCreate}</strong> plan{totalPlansToCreate > 1 ? 'es' : ''}: {selectedUserIds.length} persona{selectedUserIds.length > 1 ? 's' : ''} × {selectedMonths.length} mes{selectedMonths.length > 1 ? 'es' : ''}
                {loadActivities && ' (con actividades precargadas)'}
              </span>
            }
            style={{ marginTop: 8 }}
          />
        )}
      </Modal>
    </div>
  );
};

export default PlanningListPage;
