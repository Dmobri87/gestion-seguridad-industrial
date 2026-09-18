import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table, Button, Card, Select, Space, Tag, Progress, Modal,
  message, Typography, Checkbox, Row, Col, Divider, Alert, Switch, Input, Popconfirm
} from 'antd';
import { PlusOutlined, EyeOutlined, CheckOutlined, TeamOutlined, SearchOutlined, DeleteOutlined } from '@ant-design/icons';
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
  const [loadingAudit, setLoadingAudit] = useState(false);
  const [plans, setPlans] = useState<MonthlyPlan[]>([]);
  const [assignableUsers, setAssignableUsers] = useState<User[]>([]);
  const [workGroups, setWorkGroups] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [year, setYear] = useState(dayjs().year());
  const [month, setMonth] = useState<number | undefined>(dayjs().month() + 1);
  const [modalOpen, setModalOpen] = useState(false);
  const [auditModalOpen, setAuditModalOpen] = useState(false);

  // Estado del formulario de creación masiva
  const [selectedYear, setSelectedYear] = useState(dayjs().year());
  const [selectedMonths, setSelectedMonths] = useState<number[]>([]);
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([]);
  const [loadActivities, setLoadActivities] = useState(true);

  // Mi Plan (Coordinador)
  const [myPlanModalOpen, setMyPlanModalOpen] = useState(false);
  const [myPlanYear, setMyPlanYear] = useState(dayjs().year());
  const [myPlanMonth, setMyPlanMonth] = useState(dayjs().month() + 1);
  const [creatingMyPlan, setCreatingMyPlan] = useState(false);

  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const isCoordinator = ['Administrador', 'Coordinador'].includes(user?.role || '');
  const isAdmin = user?.role === 'Administrador';

  useEffect(() => {
    loadPlans();
    if (isCoordinator) {
      loadAssignableUsers();
      loadWorkGroups();
    }
  }, [year, month]);

  const handleCreateMyPlan = async () => {
    setCreatingMyPlan(true);
    try {
      const plan = await planningApi.createPlan({
        user_id: user!.id,
        year: myPlanYear,
        month: myPlanMonth,
        organization_id: user!.organization_id,
      });
      message.success('Plan de coordinador creado');
      setMyPlanModalOpen(false);
      navigate(`/planificacion/${plan.id}`);
    } catch (error: any) {
      message.error(error?.response?.data?.detail || 'Error al crear el plan');
    } finally {
      setCreatingMyPlan(false);
    }
  };

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

  const [groupRoleFilter, setGroupRoleFilter] = useState<string | null>('TAE');

  const handleSelectByGroup = (groupId: number) => {
    let groupMembers = assignableUsers.filter((u: any) => u.work_group_id === groupId);
    // Aplicar filtro de rol si está activo
    if (groupRoleFilter) {
      groupMembers = groupMembers.filter((u) => u.role === groupRoleFilter);
    }
    const memberIds = groupMembers.map((u) => u.id);
    if (memberIds.length === 0) return;
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
    setGroupRoleFilter('TAE');
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

  const handleDeletePlan = async (planId: number) => {
    try {
      await planningApi.deletePlan(planId);
      message.success('Plan eliminado');
      loadPlans();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al eliminar el plan');
    }
  };

  const handleViewPlan = (record: MonthlyPlan) => {
    if (!record?.id || Number.isNaN(Number(record.id))) {
      message.error('ID de plan inválido');
      return;
    }
    navigate(`/planificacion/${record.id}`);
  };

  const loadAuditLogs = async () => {
    setLoadingAudit(true);
    try {
      const response = await planningApi.getDeletionAuditLogs(200);
      setAuditLogs(response);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al cargar auditoría');
    } finally {
      setLoadingAudit(false);
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
      sorter: (a: MonthlyPlan, b: MonthlyPlan) => (a.user_name || '').localeCompare(b.user_name || ''),
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: any) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="Buscar personal"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button type="primary" onClick={() => confirm()} icon={<SearchOutlined />} size="small">Buscar</Button>
            <Button onClick={() => { clearFilters?.(); confirm(); }} size="small">Limpiar</Button>
          </Space>
        </div>
      ),
      filterIcon: (filtered: boolean) => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value: any, record: MonthlyPlan) =>
        (record.user_name || '').toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: 'Período',
      key: 'period',
      render: (_: any, record: MonthlyPlan) => (
        <span>{MONTHS.find((m) => m.value === record.month)?.label} {record.year}</span>
      ),
      sorter: (a: MonthlyPlan, b: MonthlyPlan) => {
        const aVal = a.year * 100 + a.month;
        const bVal = b.year * 100 + b.month;
        return aVal - bVal;
      },
      filters: MONTHS.map(m => ({ text: m.label, value: m.value })),
      onFilter: (value: any, record: MonthlyPlan) => record.month === value,
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
      filters: [
        { text: 'Borrador', value: 'Borrador' },
        { text: 'Aprobado', value: 'Aprobado' },
        { text: 'Cancelado', value: 'Cancelado' },
      ],
      onFilter: (value: any, record: MonthlyPlan) => record.status === value,
    },
    {
      title: 'Planeado',
      dataIndex: 'total_planned',
      key: 'total_planned',
      align: 'center' as const,
      sorter: (a: MonthlyPlan, b: MonthlyPlan) => a.total_planned - b.total_planned,
    },
    {
      title: 'Ejecutado',
      dataIndex: 'total_executed',
      key: 'total_executed',
      align: 'center' as const,
      sorter: (a: MonthlyPlan, b: MonthlyPlan) => a.total_executed - b.total_executed,
    },
    {
      title: 'Cumplimiento',
      dataIndex: 'compliance_percentage',
      key: 'compliance_percentage',
      sorter: (a: MonthlyPlan, b: MonthlyPlan) => a.compliance_percentage - b.compliance_percentage,
      render: (value: number) => (
        <Progress
          percent={Number(value.toFixed(0))}
          size="small"
          strokeColor={getComplianceColor(value)}
          style={{ minWidth: 100 }}
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
            onClick={() => handleViewPlan(record)}
          >
            Ver
          </Button>
          {isCoordinator && record.status === 'Borrador' && (
            <Button
              type="link"
              icon={<CheckOutlined />}
              onClick={() => handleApprovePlan(record.id)}
              style={{ color: '#52c41a' }}
            >
              Aprobar
            </Button>
          )}
          {isAdmin && (
            <Popconfirm
              title="Eliminar plan mensual"
              description="Esta acción eliminará el plan completo si no tiene ejecuciones. ¿Continuar?"
              onConfirm={() => handleDeletePlan(record.id)}
              okText="Eliminar"
              cancelText="Cancelar"
            >
              <Button type="link" danger icon={<DeleteOutlined />}>
                Eliminar
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
          <Title level={4} style={{ margin: 0, whiteSpace: 'nowrap', flexShrink: 0 }}>Planes Mensuales</Title>

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
                icon={<PlusOutlined />}
                onClick={() => {
                  setMyPlanYear(year);
                  setMyPlanMonth(month || dayjs().month() + 1);
                  setMyPlanModalOpen(true);
                }}
              >
                Mi Plan
              </Button>
            )}
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
            {isAdmin && (
              <Button
                onClick={() => {
                  setAuditModalOpen(true);
                  loadAuditLogs();
                }}
              >
                Auditoría
              </Button>
            )}
          </Space>
        </div>

        <Table
          dataSource={plans}
          columns={columns}
          rowKey="id"
          loading={loading}
          scroll={{ x: 700 }}
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
        maskClosable={false}
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

          {/* Filtro de rol para selección por grupo */}
          {workGroups.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>Por grupo</Text>
                <Select
                  size="small"
                  value={groupRoleFilter}
                  onChange={setGroupRoleFilter}
                  allowClear
                  placeholder="Todos los roles"
                  style={{ width: 140, fontSize: 12 }}
                  options={[
                    { value: 'TAE', label: 'Solo TAEs' },
                    { value: 'PSE', label: 'Solo PSEs' },
                    { value: 'Supervisor', label: 'Solo Supervisores' },
                  ]}
                />
              </div>
              <div style={{ marginTop: 4 }}>
                <Space wrap>
                  {workGroups.map((g: any) => (
                    <Button
                      key={g.id}
                      size="small"
                      type={
                        (() => {
                          let members = assignableUsers.filter((u: any) => u.work_group_id === g.id);
                          if (groupRoleFilter) members = members.filter((u) => u.role === groupRoleFilter);
                          return members.length > 0 && members.every((u) => selectedUserIds.includes(u.id));
                        })() ? 'primary' : 'default'
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

      <Modal
        title="Auditoría de Eliminaciones"
        open={auditModalOpen}
        onCancel={() => setAuditModalOpen(false)}
        footer={null}
        width={1000}
      >
        <Table
          dataSource={auditLogs}
          loading={loadingAudit}
          rowKey="id"
          size="small"
          scroll={{ x: 900 }}
          pagination={{ pageSize: 10 }}
          columns={[
            {
              title: 'Fecha',
              dataIndex: 'created_at',
              key: 'created_at',
              width: 160,
              render: (value: string) => dayjs(value).format('DD/MM/YYYY HH:mm'),
            },
            {
              title: 'Usuario',
              dataIndex: 'user_email',
              key: 'user_email',
              width: 220,
            },
            {
              title: 'Tipo',
              dataIndex: 'resource_type',
              key: 'resource_type',
              width: 150,
              render: (value: string) => (
                <Tag color={value === 'monthly_plan' ? 'purple' : 'blue'}>
                  {value === 'monthly_plan' ? 'Plan Mensual' : 'Actividad'}
                </Tag>
              ),
            },
            {
              title: 'ID Recurso',
              dataIndex: 'resource_id',
              key: 'resource_id',
              width: 100,
            },
            {
              title: 'Detalle',
              dataIndex: 'description',
              key: 'description',
            },
          ]}
        />
      </Modal>
      {/* ==========================================
          MODAL MI PLAN (COORDINADOR)
          ========================================== */}
      <Modal
        title="Crear Mi Plan de Trabajo"
        open={myPlanModalOpen}
        onCancel={() => setMyPlanModalOpen(false)}
        onOk={handleCreateMyPlan}
        okText="Crear Plan"
        okButtonProps={{ loading: creatingMyPlan }}
        cancelText="Cancelar"
        width={400}
      >
        <Space direction="vertical" style={{ width: '100%' }} size={16}>
          <div>
            <Text strong>Año</Text>
            <div style={{ marginTop: 8 }}>
              <Select
                value={myPlanYear}
                onChange={setMyPlanYear}
                options={[
                  { value: 2025, label: '2025' },
                  { value: 2026, label: '2026' },
                  { value: 2027, label: '2027' },
                ]}
                style={{ width: '100%' }}
              />
            </div>
          </div>
          <div>
            <Text strong>Mes</Text>
            <div style={{ marginTop: 8 }}>
              <Select
                value={myPlanMonth}
                onChange={setMyPlanMonth}
                options={MONTHS}
                style={{ width: '100%' }}
              />
            </div>
          </div>
          <Alert
            type="info"
            showIcon
            message="Se creará un plan de trabajo personal para el coordinador con las actividades de VERIFICAR, REALIZAR, REVISA y OTROS."
          />
        </Space>
      </Modal>
    </div>
  );
};

export default PlanningListPage;
