import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Select, Space, Tag, Modal, Form, Input, message,
  Typography, Row, Col, Statistic, Tabs, Descriptions, Switch, Tooltip, Divider, Progress, Grid,
  Timeline, Alert, InputNumber
} from 'antd';
import {
  PlusOutlined, ToolOutlined, WarningOutlined, CheckCircleOutlined, EditOutlined,
  SunOutlined, MoonOutlined, CarOutlined, EnvironmentOutlined, DashboardOutlined,
  ExclamationCircleOutlined, ClockCircleOutlined, HistoryOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import relativeTime from 'dayjs/plugin/relativeTime';
import { equipmentApi } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

dayjs.extend(duration);
dayjs.extend(relativeTime);

const { Title, Text } = Typography;
const { TextArea } = Input;
const { useBreakpoint } = Grid;

interface Equipment {
  id: number;
  category_id: number;
  category_name: string | null;
  code: string;
  name: string;
  status: string;
  location: string | null;
  last_maintenance_date: string | null;
  next_maintenance_date: string | null;
  is_available_day: boolean;
  is_available_night: boolean;
  description: string | null;
  notes: string | null;
  active_novelty: string | null;
  active_novelty_id: number | null;
  novelties_count: number;
}

interface EquipmentCategory {
  id: number;
  name: string;
  code: string;
  color: string;
}

interface Novelty {
  id: number;
  equipment_id: number;
  novelty_type: string;
  description: string;
  shift: string;
  unavailable_hours: number;
  start_date: string;
  end_date: string | null;
  is_resolved: boolean;
  resolution: string | null;
  previous_status: string | null;
  reported_by: number;
  reporter_name: string | null;
  resolved_by: number | null;
  resolver_name: string | null;
  created_at: string;
}

interface FleetData {
  total: number;
  operational: number;
  available_day: number;
  available_night: number;
  by_category: {
    category_id: number;
    category_name: string;
    total: number;
    operational: number;
    available_day: number;
    available_night: number;
    in_maintenance: number;
    out_of_service: number;
  }[];
  by_location: {
    location: string;
    total: number;
    available_day: number;
    available_night: number;
  }[];
}

const EquipmentPage = () => {
  const screens = useBreakpoint();
  const [loading, setLoading] = useState(true);
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [categories, setCategories] = useState<EquipmentCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number | undefined>(undefined);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEquipment, setEditingEquipment] = useState<Equipment | null>(null);
  const [detailModal, setDetailModal] = useState<Equipment | null>(null);
  const [form] = Form.useForm();
  const user = useAuthStore((state) => state.user);

  // Flota
  const [fleet, setFleet] = useState<FleetData | null>(null);

  // Novedades
  const [noveltyModalOpen, setNoveltyModalOpen] = useState(false);
  const [noveltyEquipment, setNoveltyEquipment] = useState<Equipment | null>(null);
  const [novelties, setNovelties] = useState<Novelty[]>([]);
  const [noveltiesLoading, setNoveltiesLoading] = useState(false);
  const [noveltyForm] = Form.useForm();

  // Resolver novedad
  const [resolveModalOpen, setResolveModalOpen] = useState(false);
  const [resolvingNovelty, setResolvingNovelty] = useState<Novelty | null>(null);
  const [resolveForm] = Form.useForm();

  const canManage = ['Administrador', 'Coordinador'].includes(user?.role || '');

  useEffect(() => {
    loadEquipment();
    loadCategories();
    loadFleet();
  }, [selectedCategory]);

  const loadEquipment = async () => {
    setLoading(true);
    try {
      const response = await equipmentApi.getAll(selectedCategory);
      setEquipment(response);
    } catch (error) {
      console.error('Error loading equipment:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const response = await equipmentApi.getCategories();
      setCategories(response);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadFleet = async () => {
    try {
      const response = await equipmentApi.getFleet();
      setFleet(response);
    } catch (error) {
      console.error('Error loading fleet:', error);
    }
  };

  // ==========================================
  // CREAR / EDITAR EQUIPO
  // ==========================================

  const openCreateModal = () => {
    setEditingEquipment(null);
    form.resetFields();
    form.setFieldsValue({ status: 'Operativo', is_available_day: true, is_available_night: true });
    setModalOpen(true);
  };

  const openEditModal = (eq: Equipment) => {
    setEditingEquipment(eq);
    form.setFieldsValue({
      ...eq,
      next_maintenance_date: eq.next_maintenance_date || undefined,
    });
    setModalOpen(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      const payload = { ...values, next_maintenance_date: values.next_maintenance_date || null };
      if (editingEquipment) {
        await equipmentApi.update(editingEquipment.id, payload);
        message.success('Equipo actualizado');
      } else {
        await equipmentApi.create(payload);
        message.success('Equipo registrado');
      }
      setModalOpen(false);
      form.resetFields();
      setEditingEquipment(null);
      loadEquipment();
      loadFleet();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al guardar');
    }
  };

  // ==========================================
  // NOVEDADES
  // ==========================================

  const openNoveltyPanel = async (eq: Equipment) => {
    setNoveltyEquipment(eq);
    setNoveltyModalOpen(true);
    setNoveltiesLoading(true);
    try {
      const response = await equipmentApi.getNovelties(eq.id);
      setNovelties(response);
    } catch (error) {
      console.error('Error loading novelties:', error);
      setNovelties([]);
    } finally {
      setNoveltiesLoading(false);
    }
  };

  const handleCreateNovelty = async (values: any) => {
    if (!noveltyEquipment) return;
    try {
      await equipmentApi.createNovelty(noveltyEquipment.id, {
        ...values,
        start_date: new Date().toISOString(),
      });
      message.success('Novedad registrada');
      noveltyForm.resetFields();
      // Recargar
      const updated = await equipmentApi.getNovelties(noveltyEquipment.id);
      setNovelties(updated);
      loadEquipment();
      loadFleet();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al registrar novedad');
    }
  };

  const openResolveModal = (novelty: Novelty) => {
    setResolvingNovelty(novelty);
    resolveForm.resetFields();
    setResolveModalOpen(true);
  };

  const handleResolveNovelty = async (values: any) => {
    if (!resolvingNovelty || !noveltyEquipment) return;
    try {
      await equipmentApi.resolveNovelty(noveltyEquipment.id, resolvingNovelty.id, values);
      message.success('Novedad resuelta — equipo vuelve a servicio');
      setResolveModalOpen(false);
      setResolvingNovelty(null);
      // Recargar
      const updated = await equipmentApi.getNovelties(noveltyEquipment.id);
      setNovelties(updated);
      loadEquipment();
      loadFleet();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al resolver');
    }
  };

  const getElapsedTime = (startDate: string) => {
    const start = dayjs(startDate);
    const diff = dayjs().diff(start, 'hour', true);
    if (diff < 1) return `${Math.round(diff * 60)} min`;
    if (diff < 24) return `${Math.round(diff)} horas`;
    return `${Math.floor(diff / 24)} días ${Math.round(diff % 24)}h`;
  };

  // ==========================================
  // HELPERS DE RENDERIZADO
  // ==========================================

  const getStatusTag = (status: string) => {
    const config: Record<string, { color: string; icon: React.ReactNode }> = {
      Operativo: { color: 'green', icon: <CheckCircleOutlined /> },
      'En Mantenimiento': { color: 'orange', icon: <ToolOutlined /> },
      'Fuera de Servicio': { color: 'red', icon: <WarningOutlined /> },
      'Dado de Baja': { color: 'default', icon: <WarningOutlined /> },
    };
    const c = config[status] || { color: 'default', icon: null };
    return <Tag color={c.color} icon={c.icon}>{status}</Tag>;
  };

  const getAvailabilityIndicator = (eq: Equipment) => {
    const mobile = !screens.md;
    if (eq.status !== 'Operativo') return <Tag color="default">No disponible</Tag>;
    const day = eq.is_available_day;
    const night = eq.is_available_night;
    if (day && night) {
      return (
        <Space size={4}>
          <Tag color="green"><SunOutlined />{!mobile && ' Día'}</Tag>
          <Tag color="blue"><MoonOutlined />{!mobile && ' Noche'}</Tag>
        </Space>
      );
    }
    if (day) return <Tag color="green"><SunOutlined />{!mobile && ' Solo Día'}</Tag>;
    if (night) return <Tag color="blue"><MoonOutlined />{!mobile && ' Solo Noche'}</Tag>;
    return <Tag color="red">Sin turno</Tag>;
  };

  // ==========================================
  // COLUMNAS
  // ==========================================

  const columns = [
    {
      title: 'N°', key: 'rowNumber', width: 50, fixed: 'left' as const, align: 'center' as const,
      render: (_: any, __: Equipment, index: number) => <Text type="secondary">{index + 1}</Text>,
    },
    { title: 'Código', dataIndex: 'code', key: 'code', width: 100, render: (code: string) => <Text strong>{code}</Text> },
    {
      title: 'Nombre', dataIndex: 'name', key: 'name', width: 140, ellipsis: true,
      render: (name: string, record: Equipment) => (
        <div>
          <div>{name}</div>
          {record.active_novelty && (
            <Text type="danger" style={{ fontSize: 11 }}>
              <ExclamationCircleOutlined /> {record.active_novelty}
            </Text>
          )}
        </div>
      ),
    },
    { title: 'Categoría', dataIndex: 'category_name', key: 'category', width: 140, render: (val: string | null) => val || '-' },
    {
      title: 'Ubicación', dataIndex: 'location', key: 'location', width: 130, ellipsis: true,
      render: (loc: string | null) => loc ? <span><EnvironmentOutlined style={{ marginRight: 4 }} />{loc}</span> : '-',
    },
    { title: 'Estado', dataIndex: 'status', key: 'status', width: 110, render: (status: string) => getStatusTag(status) },
    { title: 'Disponibilidad', key: 'availability', width: 100, render: (_: any, record: Equipment) => getAvailabilityIndicator(record) },
    {
      title: 'Próx. Mantto.', dataIndex: 'next_maintenance_date', key: 'maintenance', width: 110,
      render: (d: string | null) => {
        if (!d) return '-';
        const du = dayjs(d).diff(dayjs(), 'day');
        return <Text type={du < 0 ? 'danger' : du < 15 ? 'warning' : undefined}>{dayjs(d).format('DD/MM/YYYY')}</Text>;
      },
    },
    {
      title: 'Acciones', key: 'actions', width: 100,
      render: (_: any, record: Equipment) => (
        <Space size="small">
          <Button type="link" size="small" onClick={() => setDetailModal(record)}>Ver</Button>
          {canManage && <Tooltip title="Editar"><Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)} /></Tooltip>}
          <Tooltip title="Novedades">
            <Button type="link" size="small" icon={<HistoryOutlined />} onClick={() => openNoveltyPanel(record)}
              style={record.active_novelty ? { color: '#ff4d4f' } : undefined}>
              {record.novelties_count > 0 ? record.novelties_count : ''}
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ];

  const totalEquipment = equipment.length;
  const operativeCount = equipment.filter(e => e.status === 'Operativo').length;
  const outOfServiceCount = equipment.filter(e => e.status !== 'Operativo').length;
  return (
    <div>
      {/* Stats */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card size="small"><Statistic title="Total Equipos" value={totalEquipment} prefix={<ToolOutlined />} /></Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="Operativos" value={operativeCount} suffix={`/ ${totalEquipment}`}
              valueStyle={{ color: '#3f8600' }} prefix={<CheckCircleOutlined />} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="Disp. Turno Día" value={fleet?.available_day || 0}
              prefix={<SunOutlined />} valueStyle={{ color: '#fa8c16' }}
              suffix={<Text type="secondary" style={{ fontSize: 14 }}>/ {fleet?.total || 0}</Text>} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="Disp. Turno Noche" value={fleet?.available_night || 0}
              prefix={<MoonOutlined />} valueStyle={{ color: '#1890ff' }}
              suffix={<Text type="secondary" style={{ fontSize: 14 }}>/ {fleet?.total || 0}</Text>} />
          </Card>
        </Col>
      </Row>

      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
          <Title level={4} style={{ margin: 0, whiteSpace: 'nowrap', flexShrink: 0 }}><ToolOutlined style={{ marginRight: 8 }} />Inventario de Equipos</Title>
          <Space>
            <Select value={selectedCategory} onChange={setSelectedCategory} style={{ width: 200 }}
              placeholder="Todas las categorías" allowClear
              options={categories.map(c => ({ value: c.id, label: c.name }))} />
            {canManage && (
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>Agregar Equipo</Button>
            )}
          </Space>
        </div>

        <Tabs defaultActiveKey="all" size="small" items={[
          {
            key: 'all', label: `Todos (${totalEquipment})`,
            children: <Table dataSource={equipment} columns={columns} rowKey="id" loading={loading}
              scroll={{ x: 'max-content' }}
              pagination={{ defaultPageSize: 15, showSizeChanger: true, pageSizeOptions: ['15', '20', '50', '100'] }} size="small" />,
          },
          {
            key: 'operative', label: <span style={{ color: '#52c41a' }}>Operativos ({operativeCount})</span>,
            children: <Table dataSource={equipment.filter(e => e.status === 'Operativo')} columns={columns} rowKey="id"
              loading={loading} scroll={{ x: 'max-content' }}
              pagination={{ defaultPageSize: 15, showSizeChanger: true, pageSizeOptions: ['15', '20', '50', '100'] }} size="small" />,
          },
          {
            key: 'out', label: <span style={{ color: outOfServiceCount > 0 ? '#ff4d4f' : undefined }}>Fuera de Servicio ({outOfServiceCount})</span>,
            children: <Table dataSource={equipment.filter(e => e.status !== 'Operativo')} columns={columns} rowKey="id"
              loading={loading} scroll={{ x: 'max-content' }}
              pagination={{ defaultPageSize: 15, showSizeChanger: true, pageSizeOptions: ['15', '20', '50', '100'] }} size="small" />,
          },
          {
            key: 'fleet', label: <span><DashboardOutlined /> Flota por Turnos</span>,
            children: fleet ? (
              <div>
                <Row gutter={16} style={{ marginBottom: 24 }}>
                  <Col span={6}><Card size="small" style={{ textAlign: 'center', borderTop: '3px solid #1890ff' }}>
                    <Statistic title="Total Flota" value={fleet.total} prefix={<CarOutlined />} /></Card></Col>
                  <Col span={6}><Card size="small" style={{ textAlign: 'center', borderTop: '3px solid #52c41a' }}>
                    <Statistic title="Operativos" value={fleet.operational} valueStyle={{ color: '#52c41a' }} />
                    <Progress percent={fleet.total > 0 ? Math.round((fleet.operational / fleet.total) * 100) : 0} size="small" strokeColor="#52c41a" /></Card></Col>
                  <Col span={6}><Card size="small" style={{ textAlign: 'center', borderTop: '3px solid #fa8c16' }}>
                    <Statistic title={<span><SunOutlined /> Turno Día</span>} value={fleet.available_day} valueStyle={{ color: '#fa8c16' }} suffix={`/ ${fleet.total}`} />
                    <Progress percent={fleet.total > 0 ? Math.round((fleet.available_day / fleet.total) * 100) : 0} size="small" strokeColor="#fa8c16" /></Card></Col>
                  <Col span={6}><Card size="small" style={{ textAlign: 'center', borderTop: '3px solid #1890ff' }}>
                    <Statistic title={<span><MoonOutlined /> Turno Noche</span>} value={fleet.available_night} valueStyle={{ color: '#1890ff' }} suffix={`/ ${fleet.total}`} />
                    <Progress percent={fleet.total > 0 ? Math.round((fleet.available_night / fleet.total) * 100) : 0} size="small" strokeColor="#1890ff" /></Card></Col>
                </Row>
                <Title level={5} style={{ marginBottom: 12 }}>Disponibilidad por Categoría</Title>
                <Table dataSource={fleet.by_category} rowKey="category_id" pagination={false} size="small" scroll={{ x: 600 }} style={{ marginBottom: 24 }}
                  columns={[
                    { title: 'Categoría', dataIndex: 'category_name', key: 'cat' },
                    { title: 'Total', dataIndex: 'total', key: 'total', width: 80, align: 'center' as const },
                    { title: 'Operativos', dataIndex: 'operational', key: 'op', width: 100, align: 'center' as const, render: (v: number) => <Tag color="green">{v}</Tag> },
                    { title: <span><SunOutlined /> Día</span>, dataIndex: 'available_day', key: 'day', width: 90, align: 'center' as const,
                      render: (v: number, r: any) => <span style={{ color: '#fa8c16', fontWeight: 600 }}>{v} <Text type="secondary">/ {r.total}</Text></span> },
                    { title: <span><MoonOutlined /> Noche</span>, dataIndex: 'available_night', key: 'night', width: 100, align: 'center' as const,
                      render: (v: number, r: any) => <span style={{ color: '#1890ff', fontWeight: 600 }}>{v} <Text type="secondary">/ {r.total}</Text></span> },
                    { title: 'En Mantto.', dataIndex: 'in_maintenance', key: 'maint', width: 100, align: 'center' as const, render: (v: number) => v > 0 ? <Tag color="orange">{v}</Tag> : <span>0</span> },
                    { title: 'Fuera Serv.', dataIndex: 'out_of_service', key: 'oos', width: 100, align: 'center' as const, render: (v: number) => v > 0 ? <Tag color="red">{v}</Tag> : <span>0</span> },
                  ]} />
                <Title level={5} style={{ marginBottom: 12 }}>Disponibilidad por Ubicación (CAE)</Title>
                <Table dataSource={fleet.by_location} rowKey="location" pagination={false} size="small" scroll={{ x: 600 }}
                  columns={[
                    { title: 'Ubicación / CAE', dataIndex: 'location', key: 'loc', render: (v: string) => <span><EnvironmentOutlined style={{ marginRight: 4 }} />{v}</span> },
                    { title: 'Total Equipos', dataIndex: 'total', key: 'total', width: 120, align: 'center' as const },
                    { title: <span><SunOutlined /> Disponibles Día</span>, dataIndex: 'available_day', key: 'day', width: 160, align: 'center' as const,
                      render: (v: number, r: any) => <div><span style={{ color: '#fa8c16', fontWeight: 600, fontSize: 16 }}>{v}</span><Text type="secondary"> / {r.total}</Text>
                        <Progress percent={r.total > 0 ? Math.round((v / r.total) * 100) : 0} size="small" strokeColor="#fa8c16" showInfo={false} style={{ marginTop: 2 }} /></div> },
                    { title: <span><MoonOutlined /> Disponibles Noche</span>, dataIndex: 'available_night', key: 'night', width: 160, align: 'center' as const,
                      render: (v: number, r: any) => <div><span style={{ color: '#1890ff', fontWeight: 600, fontSize: 16 }}>{v}</span><Text type="secondary"> / {r.total}</Text>
                        <Progress percent={r.total > 0 ? Math.round((v / r.total) * 100) : 0} size="small" strokeColor="#1890ff" showInfo={false} style={{ marginTop: 2 }} /></div> },
                  ]} />
              </div>
            ) : <div style={{ textAlign: 'center', padding: 40 }}>Cargando datos de flota...</div>,
          },
        ]} />
      </Card>

      {/* ===== MODAL CREAR / EDITAR EQUIPO ===== */}
      <Modal title={editingEquipment ? 'Editar Equipo' : 'Agregar Equipo'} open={modalOpen}
        onCancel={() => { setModalOpen(false); setEditingEquipment(null); form.resetFields(); }}
        onOk={() => form.submit()} okText={editingEquipment ? 'Guardar Cambios' : 'Agregar'} cancelText="Cancelar" width={650}>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="category_id" label="Categoría" rules={[{ required: true, message: 'Selecciona categoría' }]}>
                <Select placeholder="Selecciona categoría" options={categories.map(c => ({ value: c.id, label: c.name }))} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="code" label="Código" rules={[{ required: true, message: 'Ingresa el código' }]}>
                <Input placeholder="Ej: AMB-001" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="name" label="Nombre del Equipo" rules={[{ required: true, message: 'Ingresa el nombre' }]}>
            <Input placeholder="Ej: Ambulancia TAB Tipo II" />
          </Form.Item>
          <Form.Item name="description" label="Descripción">
            <TextArea rows={2} placeholder="Descripción del equipo..." />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="location" label="Ubicación / CAE" rules={[{ required: true, message: 'Ingresa ubicación' }]}>
                <Input placeholder="Ej: CAE Norte" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="Estado" rules={[{ required: true }]} initialValue="Operativo">
                <Select options={[
                  { value: 'Operativo', label: 'Operativo' },
                  { value: 'En Mantenimiento', label: 'En Mantenimiento' },
                  { value: 'Fuera de Servicio', label: 'Fuera de Servicio' },
                  { value: 'Dado de Baja', label: 'Dado de Baja' },
                ]} />
              </Form.Item>
            </Col>
          </Row>
          <Divider style={{ margin: '8px 0 16px' }}>Disponibilidad por Turno</Divider>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="is_available_day" label={<span><SunOutlined style={{ color: '#fa8c16' }} /> Turno Día (06:00 - 18:00)</span>}
                valuePropName="checked" initialValue={true}>
                <Switch checkedChildren="Disponible" unCheckedChildren="No disponible" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="is_available_night" label={<span><MoonOutlined style={{ color: '#1890ff' }} /> Turno Noche (18:00 - 06:00)</span>}
                valuePropName="checked" initialValue={true}>
                <Switch checkedChildren="Disponible" unCheckedChildren="No disponible" />
              </Form.Item>
            </Col>
          </Row>
          <Divider style={{ margin: '8px 0 16px' }}>Mantenimiento</Divider>
          <Form.Item name="next_maintenance_date" label="Próximo Mantenimiento">
            <Input type="date" />
          </Form.Item>
          <Form.Item name="notes" label="Notas adicionales">
            <TextArea rows={2} placeholder="Notas sobre el equipo..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* ===== MODAL DETALLE ===== */}
      <Modal title="Detalle del Equipo" open={!!detailModal} onCancel={() => setDetailModal(null)} width={650}
        footer={canManage ? [
          <Button key="novelty" icon={<ExclamationCircleOutlined />}
            onClick={() => { setDetailModal(null); openNoveltyPanel(detailModal!); }}
            danger={!!detailModal?.active_novelty}>
            Novedades
          </Button>,
          <Button key="edit" type="primary" icon={<EditOutlined />}
            onClick={() => { const eq = detailModal; setDetailModal(null); openEditModal(eq!); }}>Editar</Button>,
          <Button key="close" onClick={() => setDetailModal(null)}>Cerrar</Button>,
        ] : [<Button key="close" onClick={() => setDetailModal(null)}>Cerrar</Button>]}>
        {detailModal && (
          <div>
            {detailModal.active_novelty && (
              <Alert type="error" showIcon style={{ marginBottom: 16 }}
                icon={<ExclamationCircleOutlined />}
                message={<Text strong>Equipo con novedad activa</Text>}
                description={detailModal.active_novelty} />
            )}
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="Código"><Text strong>{detailModal.code}</Text></Descriptions.Item>
              <Descriptions.Item label="Categoría">{detailModal.category_name}</Descriptions.Item>
              <Descriptions.Item label="Nombre" span={2}>{detailModal.name}</Descriptions.Item>
              {detailModal.description && <Descriptions.Item label="Descripción" span={2}>{detailModal.description}</Descriptions.Item>}
              <Descriptions.Item label="Ubicación"><EnvironmentOutlined style={{ marginRight: 4 }} />{detailModal.location || '-'}</Descriptions.Item>
              <Descriptions.Item label="Estado">{getStatusTag(detailModal.status)}</Descriptions.Item>
              <Descriptions.Item label="Disponibilidad" span={2}>{getAvailabilityIndicator(detailModal)}</Descriptions.Item>
              <Descriptions.Item label="Último Mantto.">{detailModal.last_maintenance_date ? dayjs(detailModal.last_maintenance_date).format('DD/MM/YYYY') : '-'}</Descriptions.Item>
              <Descriptions.Item label="Próximo Mantto.">{detailModal.next_maintenance_date ? dayjs(detailModal.next_maintenance_date).format('DD/MM/YYYY') : '-'}</Descriptions.Item>
              {detailModal.notes && <Descriptions.Item label="Notas" span={2}>{detailModal.notes}</Descriptions.Item>}
            </Descriptions>
          </div>
        )}
      </Modal>

      {/* ===== MODAL NOVEDADES / HISTORIAL ===== */}
      <Modal
        title={<Space><HistoryOutlined /><span>Novedades — {noveltyEquipment?.code} {noveltyEquipment?.name}</span></Space>}
        open={noveltyModalOpen}
        onCancel={() => { setNoveltyModalOpen(false); setNoveltyEquipment(null); setNovelties([]); noveltyForm.resetFields(); }}
        footer={null} width={700}>

        {/* Novedad activa */}
        {noveltyEquipment?.active_novelty && (
          <Alert type="error" showIcon style={{ marginBottom: 16 }}
            icon={<ClockCircleOutlined />}
            message={
              <Space>
                <Text strong style={{ color: '#ff4d4f' }}>FUERA DE SERVICIO</Text>
                <Tag color="red">{novelties.find(n => !n.is_resolved)?.shift || ''}</Tag>
              </Space>
            }
            description={
              <div>
                <div>{noveltyEquipment.active_novelty}</div>
                {novelties.find(n => !n.is_resolved) && (
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary">Desde: {dayjs(novelties.find(n => !n.is_resolved)!.start_date).format('DD/MM/YYYY HH:mm')}</Text>
                    <Text strong style={{ marginLeft: 12, color: '#ff4d4f' }}>
                      <ClockCircleOutlined /> {getElapsedTime(novelties.find(n => !n.is_resolved)!.start_date)}
                    </Text>
                  </div>
                )}
                {canManage && (
                  <Button type="primary" size="small" style={{ marginTop: 8 }}
                    onClick={() => openResolveModal(novelties.find(n => !n.is_resolved)!)}>
                    Resolver Novedad
                  </Button>
                )}
              </div>
            }
          />
        )}

        {/* Formulario nueva novedad */}
        {canManage && !noveltyEquipment?.active_novelty && (
          <Card size="small" style={{ marginBottom: 16, background: '#fafafa' }} title="Registrar Nueva Novedad">
            <Form form={noveltyForm} layout="vertical" onFinish={handleCreateNovelty}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="novelty_type" label="Tipo de Novedad" rules={[{ required: true, message: 'Selecciona tipo' }]}>
                    <Select placeholder="Tipo de novedad" options={[
                      { value: 'Fuera de Servicio', label: 'Fuera de Servicio' },
                      { value: 'En Mantenimiento', label: 'En Mantenimiento' },
                      { value: 'Siniestro', label: 'Siniestro' },
                      { value: 'Otro', label: 'Otro' },
                    ]} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="shift" label="Turno Afectado" rules={[{ required: true, message: 'Selecciona turno' }]}>
                    <Select placeholder="Turno" options={[
                      { value: 'Ambos', label: 'Ambos turnos (24h)' },
                      { value: 'Día', label: 'Turno Día (06:00-18:00)' },
                      { value: 'Noche', label: 'Turno Noche (18:00-06:00)' },
                    ]} />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name="description" label="Descripción de la Novedad" rules={[{ required: true, message: 'Describe la novedad' }]}>
                <TextArea rows={2} placeholder="Ej: Falla en sistema de frenos, se envía a taller..." />
              </Form.Item>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="unavailable_hours" label="Horas de Indisponibilidad (estimadas)" initialValue={0}>
                    <InputNumber min={0} max={999} style={{ width: '100%' }} placeholder="0" />
                  </Form.Item>
                </Col>
                <Col span={12} style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 24 }}>
                  <Button type="primary" htmlType="submit" icon={<ExclamationCircleOutlined />} danger block>
                    Registrar Novedad
                  </Button>
                </Col>
              </Row>
            </Form>
          </Card>
        )}

        {/* Historial de novedades */}
        <Divider style={{ margin: '8px 0 16px' }}>Historial de Novedades</Divider>
        {noveltiesLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>Cargando historial...</div>
        ) : novelties.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
            <CheckCircleOutlined style={{ fontSize: 32, color: '#52c41a' }} />
            <div style={{ marginTop: 8 }}>Sin novedades registradas</div>
          </div>
        ) : (
          <Timeline items={novelties.map(n => ({
            color: n.is_resolved ? 'green' : 'red',
            dot: n.is_resolved ? <CheckCircleOutlined /> : <ClockCircleOutlined style={{ color: '#ff4d4f' }} />,
            children: (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Space>
                    <Tag color={n.is_resolved ? 'default' : 'red'}>{n.novelty_type}</Tag>
                    <Tag>{n.shift}</Tag>
                    {n.unavailable_hours > 0 && <Tag color="orange"><ClockCircleOutlined /> {n.unavailable_hours}h indisponible</Tag>}
                  </Space>
                  {!n.is_resolved && <Tag color="red">ACTIVA</Tag>}
                </div>
                <Text style={{ display: 'block', margin: '4px 0' }}>{n.description}</Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {dayjs(n.start_date).format('DD/MM/YYYY HH:mm')}
                  {n.end_date && ` → ${dayjs(n.end_date).format('DD/MM/YYYY HH:mm')}`}
                  {' — '}{n.reporter_name}
                </Text>
                {n.is_resolved && n.resolution && (
                  <div style={{ marginTop: 4, padding: '4px 8px', background: '#f6ffed', borderRadius: 4, borderLeft: '3px solid #52c41a' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>Resolución:</Text>
                    <Text style={{ display: 'block', fontSize: 13 }}>{n.resolution}</Text>
                    {n.resolver_name && <Text type="secondary" style={{ fontSize: 11 }}>Resuelto por: {n.resolver_name}</Text>}
                  </div>
                )}
              </div>
            ),
          }))} />
        )}
      </Modal>

      {/* ===== MODAL RESOLVER NOVEDAD ===== */}
      <Modal title="Resolver Novedad" open={resolveModalOpen}
        onCancel={() => { setResolveModalOpen(false); setResolvingNovelty(null); }}
        onOk={() => resolveForm.submit()} okText="Resolver y Restaurar" cancelText="Cancelar">
        {resolvingNovelty && (
          <div style={{ marginBottom: 16 }}>
            <Alert type="info" showIcon
              message={`${resolvingNovelty.novelty_type} — ${resolvingNovelty.shift}`}
              description={resolvingNovelty.description} />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">Tiempo fuera de servicio: </Text>
              <Text strong>{getElapsedTime(resolvingNovelty.start_date)}</Text>
            </div>
          </div>
        )}
        <Form form={resolveForm} layout="vertical" onFinish={handleResolveNovelty}>
          <Form.Item name="resolution" label="Descripción de la Resolución" rules={[{ required: true, message: 'Describe cómo se resolvió' }]}>
            <TextArea rows={3} placeholder="Ej: Se reparó el sistema de frenos en taller autorizado..." />
          </Form.Item>
          <Form.Item name="unavailable_hours" label="Horas totales de indisponibilidad">
            <InputNumber min={0} max={9999} style={{ width: '100%' }} placeholder="Total de horas fuera de servicio" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default EquipmentPage;
