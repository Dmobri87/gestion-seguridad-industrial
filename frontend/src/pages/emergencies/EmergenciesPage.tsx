import { useState, useEffect } from 'react';
import { Card, Table, Button, Select, Space, Tag, Modal, Form, Input, message, Typography, Row, Col, Statistic, Descriptions, Timeline } from 'antd';
import { PlusOutlined, AlertOutlined, CheckCircleOutlined, ClockCircleOutlined, CarOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { emergenciesApi } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Emergency {
  id: number;
  emergency_type_id: number;
  emergency_type_name: string;
  reported_at: string;
  arrival_at: string | null;
  closed_at: string | null;
  location: string;
  description: string;
  status: string;
  priority: string;
  reporter_name: string;
  responder_name: string | null;
  actions_taken: string | null;
  result: string | null;
  response_time_minutes: number | null;
}

interface EmergencyType {
  id: number;
  name: string;
  description: string;
  priority: string;
}

const EmergenciesPage = () => {
  const [loading, setLoading] = useState(true);
  const [emergencies, setEmergencies] = useState<Emergency[]>([]);
  const [emergencyTypes, setEmergencyTypes] = useState<EmergencyType[]>([]);
  const [year, setYear] = useState(dayjs().year());
  const [month, setMonth] = useState<number | undefined>(dayjs().month() + 1);
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModal, setDetailModal] = useState<Emergency | null>(null);
  const [closeModal, setCloseModal] = useState<Emergency | null>(null);
  const [form] = Form.useForm();
  const [closeForm] = Form.useForm();
  const user = useAuthStore((state) => state.user);

  const isResponder = ['Administrador', 'Coordinador', 'TAE', 'Paramédico'].includes(user?.role || '');

  useEffect(() => {
    loadEmergencies();
    loadEmergencyTypes();
  }, [year, month]);

  const loadEmergencies = async () => {
    setLoading(true);
    try {
      const response = await emergenciesApi.getAll(year, month);
      setEmergencies(response);
    } catch (error) {
      console.error('Error loading emergencies:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadEmergencyTypes = async () => {
    try {
      const response = await emergenciesApi.getTypes();
      setEmergencyTypes(response);
    } catch (error) {
      console.error('Error loading emergency types:', error);
    }
  };

  const handleCreateEmergency = async (values: any) => {
    try {
      await emergenciesApi.create({
        emergency_type_id: values.emergency_type_id,
        organization_id: user?.organization_id,
        reported_by: user?.id,
        location: values.location,
        description: values.description,
        priority: values.priority,
      });
      message.success('Emergencia reportada');
      setModalOpen(false);
      form.resetFields();
      loadEmergencies();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al reportar');
    }
  };

  const handleRegisterArrival = async (emergencyId: number) => {
    try {
      await emergenciesApi.registerArrival(emergencyId);
      message.success('Llegada registrada');
      loadEmergencies();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error');
    }
  };

  const handleCloseEmergency = async (values: any) => {
    if (!closeModal) return;
    try {
      await emergenciesApi.close(closeModal.id, values.actions_taken, values.result);
      message.success('Emergencia cerrada');
      setCloseModal(null);
      closeForm.resetFields();
      loadEmergencies();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error');
    }
  };

  const getStatusTag = (status: string) => {
    const config: Record<string, { color: string; icon: React.ReactNode }> = {
      Reportada: { color: 'red', icon: <AlertOutlined /> },
      'En Camino': { color: 'orange', icon: <CarOutlined /> },
      'En Atención': { color: 'blue', icon: <ClockCircleOutlined /> },
      Cerrada: { color: 'green', icon: <CheckCircleOutlined /> },
    };
    const c = config[status] || { color: 'default', icon: null };
    return <Tag color={c.color} icon={c.icon}>{status}</Tag>;
  };

  const getPriorityTag = (priority: string) => {
    const colors: Record<string, string> = {
      Alta: 'red',
      Media: 'orange',
      Baja: 'blue',
    };
    return <Tag color={colors[priority] || 'default'}>{priority}</Tag>;
  };

  const columns = [
    {
      title: 'Fecha/Hora',
      dataIndex: 'reported_at',
      key: 'date',
      render: (date: string) => dayjs(date).format('DD/MM/YYYY HH:mm'),
      width: 140,
    },
    {
      title: 'Tipo',
      dataIndex: 'emergency_type_name',
      key: 'type',
    },
    {
      title: 'Ubicación',
      dataIndex: 'location',
      key: 'location',
      ellipsis: true,
    },
    {
      title: 'Prioridad',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => getPriorityTag(priority),
      width: 100,
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
      width: 130,
    },
    {
      title: 'Tiempo Resp.',
      dataIndex: 'response_time_minutes',
      key: 'response',
      render: (time: number | null) => time !== null ? `${time} min` : '-',
      width: 100,
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 200,
      render: (_: any, record: Emergency) => (
        <Space>
          <Button type="link" onClick={() => setDetailModal(record)}>Ver</Button>
          {isResponder && record.status === 'Reportada' && (
            <Button type="link" onClick={() => handleRegisterArrival(record.id)}>Llegada</Button>
          )}
          {isResponder && (record.status === 'En Camino' || record.status === 'En Atención') && (
            <Button type="link" onClick={() => setCloseModal(record)}>Cerrar</Button>
          )}
        </Space>
      ),
    },
  ];

  const activeEmergencies = emergencies.filter(e => e.status !== 'Cerrada').length;
  const avgResponseTime = emergencies
    .filter(e => e.response_time_minutes !== null)
    .reduce((acc, e, _, arr) => acc + (e.response_time_minutes || 0) / arr.length, 0);

  const months = [
    { value: undefined, label: 'Todos' },
    { value: 1, label: 'Enero' }, { value: 2, label: 'Febrero' }, { value: 3, label: 'Marzo' },
    { value: 4, label: 'Abril' }, { value: 5, label: 'Mayo' }, { value: 6, label: 'Junio' },
    { value: 7, label: 'Julio' }, { value: 8, label: 'Agosto' }, { value: 9, label: 'Septiembre' },
    { value: 10, label: 'Octubre' }, { value: 11, label: 'Noviembre' }, { value: 12, label: 'Diciembre' },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic title="Total Emergencias" value={emergencies.length} prefix={<AlertOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Activas" value={activeEmergencies} valueStyle={{ color: activeEmergencies > 0 ? '#cf1322' : '#3f8600' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Tiempo Resp. Prom." value={avgResponseTime.toFixed(1)} suffix="min" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Cerradas" value={emergencies.filter(e => e.status === 'Cerrada').length} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
      </Row>

      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <Title level={4} style={{ margin: 0 }}>Registro de Emergencias</Title>
          <Space>
            <Select value={month} onChange={setMonth} options={months} style={{ width: 140 }} />
            <Select
              value={year}
              onChange={setYear}
              options={Array.from({ length: 4 }, (_, i) => dayjs().year() - 2 + i).map(y => ({ value: y, label: String(y) }))}
              style={{ width: 100 }}
            />
            <Button type="primary" danger icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
              Reportar Emergencia
            </Button>
          </Space>
        </div>

        <Table
          dataSource={emergencies}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Modal para crear emergencia */}
      <Modal
        title="Reportar Emergencia"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        okText="Reportar"
        okButtonProps={{ danger: true }}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateEmergency}>
          <Form.Item name="emergency_type_id" label="Tipo de Emergencia" rules={[{ required: true }]}>
            <Select
              placeholder="Selecciona tipo"
              options={emergencyTypes.map((t) => ({
                value: t.id,
                label: t.name,
              }))}
            />
          </Form.Item>
          <Form.Item name="location" label="Ubicación" rules={[{ required: true }]}>
            <Input placeholder="Ej: Nivel -450, Galería Norte" />
          </Form.Item>
          <Form.Item name="priority" label="Prioridad" rules={[{ required: true }]} initialValue="Media">
            <Select options={[
              { value: 'Alta', label: 'Alta' },
              { value: 'Media', label: 'Media' },
              { value: 'Baja', label: 'Baja' },
            ]} />
          </Form.Item>
          <Form.Item name="description" label="Descripción" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="Describa la emergencia..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal de detalle */}
      <Modal
        title="Detalle de Emergencia"
        open={!!detailModal}
        onCancel={() => setDetailModal(null)}
        footer={null}
        width={600}
      >
        {detailModal && (
          <div>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="Tipo">{detailModal.emergency_type_name}</Descriptions.Item>
              <Descriptions.Item label="Estado">{getStatusTag(detailModal.status)}</Descriptions.Item>
              <Descriptions.Item label="Prioridad">{getPriorityTag(detailModal.priority)}</Descriptions.Item>
              <Descriptions.Item label="Tiempo Resp.">{detailModal.response_time_minutes ? `${detailModal.response_time_minutes} min` : '-'}</Descriptions.Item>
              <Descriptions.Item label="Ubicación" span={2}>{detailModal.location}</Descriptions.Item>
              <Descriptions.Item label="Descripción" span={2}>{detailModal.description}</Descriptions.Item>
              <Descriptions.Item label="Reportado por">{detailModal.reporter_name}</Descriptions.Item>
              <Descriptions.Item label="Atendido por">{detailModal.responder_name || '-'}</Descriptions.Item>
              {detailModal.actions_taken && (
                <Descriptions.Item label="Acciones" span={2}>{detailModal.actions_taken}</Descriptions.Item>
              )}
              {detailModal.result && (
                <Descriptions.Item label="Resultado" span={2}>{detailModal.result}</Descriptions.Item>
              )}
            </Descriptions>
            <div style={{ marginTop: 16 }}>
              <Text strong>Línea de Tiempo:</Text>
              <Timeline style={{ marginTop: 8 }}>
                <Timeline.Item color="red">Reportada: {dayjs(detailModal.reported_at).format('DD/MM/YYYY HH:mm')}</Timeline.Item>
                {detailModal.arrival_at && (
                  <Timeline.Item color="blue">Llegada: {dayjs(detailModal.arrival_at).format('DD/MM/YYYY HH:mm')}</Timeline.Item>
                )}
                {detailModal.closed_at && (
                  <Timeline.Item color="green">Cerrada: {dayjs(detailModal.closed_at).format('DD/MM/YYYY HH:mm')}</Timeline.Item>
                )}
              </Timeline>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal para cerrar emergencia */}
      <Modal
        title="Cerrar Emergencia"
        open={!!closeModal}
        onCancel={() => setCloseModal(null)}
        onOk={() => closeForm.submit()}
        okText="Cerrar Emergencia"
      >
        <Form form={closeForm} layout="vertical" onFinish={handleCloseEmergency}>
          <Form.Item name="actions_taken" label="Acciones Realizadas" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="Describa las acciones tomadas..." />
          </Form.Item>
          <Form.Item name="result" label="Resultado" rules={[{ required: true }]}>
            <Select options={[
              { value: 'Resuelto', label: 'Resuelto' },
              { value: 'Derivado', label: 'Derivado a hospital' },
              { value: 'Falsa Alarma', label: 'Falsa Alarma' },
              { value: 'Sin Consecuencias', label: 'Sin Consecuencias' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default EmergenciesPage;
