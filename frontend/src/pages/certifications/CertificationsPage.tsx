import { useState, useEffect } from 'react';
import { Card, Table, Button, Select, Tag, Modal, Form, Input, message, Typography, DatePicker, Tabs, Alert } from 'antd';
import { PlusOutlined, SafetyCertificateOutlined, WarningOutlined, UserOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { certificationsApi, usersApi } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

const { Title, Text } = Typography;

interface CertificationType {
  id: number;
  name: string;
  description: string;
  validity_months: number;
  is_required: boolean;
}

interface UserCertification {
  id: number;
  user_id: number;
  user_name: string;
  certification_type_id: number;
  certification_type_name: string;
  issue_date: string;
  expiration_date: string;
  certificate_number: string;
  issuing_entity: string;
  status: string;
  days_to_expire: number;
}

const CertificationsPage = () => {
  const [loading, setLoading] = useState(true);
  const [certifications, setCertifications] = useState<UserCertification[]>([]);
  const [expiringCerts, setExpiringCerts] = useState<UserCertification[]>([]);
  const [certTypes, setCertTypes] = useState<CertificationType[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [selectedUser, setSelectedUser] = useState<number | undefined>();
  const [form] = Form.useForm();
  const user = useAuthStore((state) => state.user);

  const canManage = ['Administrador', 'Coordinador'].includes(user?.role || '');

  useEffect(() => {
    loadCertTypes();
    loadUsers();
    loadExpiringCerts();
  }, []);

  useEffect(() => {
    if (selectedUser) {
      loadUserCertifications(selectedUser);
    } else {
      setCertifications([]);
    }
  }, [selectedUser]);

  const loadCertTypes = async () => {
    try {
      const response = await certificationsApi.getTypes();
      setCertTypes(response);
    } catch (error) {
      console.error('Error loading types:', error);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await usersApi.getTAEs();
      setUsers(response);
      setLoading(false);
    } catch (error) {
      console.error('Error loading users:', error);
      setLoading(false);
    }
  };

  const loadUserCertifications = async (userId: number) => {
    setLoading(true);
    try {
      const response = await certificationsApi.getUserCertifications(userId);
      setCertifications(response);
    } catch (error) {
      console.error('Error loading certifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadExpiringCerts = async () => {
    try {
      const response = await certificationsApi.getExpiring(60);
      setExpiringCerts(response);
    } catch (error) {
      console.error('Error loading expiring:', error);
    }
  };

  const handleCreate = async (values: any) => {
    try {
      const certType = certTypes.find(t => t.id === values.certification_type_id);
      const validityMonths = certType?.validity_months ?? 12;
      const expirationDate = dayjs(values.issue_date).add(validityMonths, 'month');

      await certificationsApi.create({
        ...values,
        issue_date: values.issue_date.format('YYYY-MM-DD'),
        expiration_date: expirationDate.format('YYYY-MM-DD'),
        organization_id: user?.organization_id,
      });
      message.success('Certificación registrada');
      setModalOpen(false);
      form.resetFields();
      if (selectedUser) loadUserCertifications(selectedUser);
      loadExpiringCerts();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al registrar');
    }
  };

  const getStatusTag = (cert: UserCertification) => {
    if (cert.status === 'Vencida' || cert.days_to_expire < 0) {
      return <Tag color="red" icon={<WarningOutlined />}>Vencida</Tag>;
    }
    if (cert.days_to_expire <= 30) {
      return <Tag color="orange" icon={<WarningOutlined />}>Por Vencer ({cert.days_to_expire} días)</Tag>;
    }
    return <Tag color="green" icon={<SafetyCertificateOutlined />}>Vigente</Tag>;
  };

  const allCertsColumns = [
    {
      title: 'TAE',
      dataIndex: 'user_name',
      key: 'user',
    },
    {
      title: 'Certificación',
      dataIndex: 'certification_type_name',
      key: 'type',
    },
    {
      title: 'N° Certificado',
      dataIndex: 'certificate_number',
      key: 'number',
    },
    {
      title: 'Emisión',
      dataIndex: 'issue_date',
      key: 'issue',
      render: (date: string) => dayjs(date).format('DD/MM/YYYY'),
    },
    {
      title: 'Vencimiento',
      dataIndex: 'expiration_date',
      key: 'expiration',
      render: (date: string) => dayjs(date).format('DD/MM/YYYY'),
    },
    {
      title: 'Estado',
      key: 'status',
      render: (_: any, record: UserCertification) => getStatusTag(record),
    },
    {
      title: 'Días',
      dataIndex: 'days_to_expire',
      key: 'days',
      render: (days: number) => (
        <Text type={days < 0 ? 'danger' : days <= 30 ? 'warning' : 'secondary'}>
          {days < 0 ? `${Math.abs(days)} vencido` : days}
        </Text>
      ),
    },
  ];

  const userCertsColumns = [
    {
      title: 'Certificación',
      dataIndex: 'certification_type_name',
      key: 'type',
    },
    {
      title: 'N° Certificado',
      dataIndex: 'certificate_number',
      key: 'number',
    },
    {
      title: 'Entidad Emisora',
      dataIndex: 'issuing_entity',
      key: 'entity',
    },
    {
      title: 'Emisión',
      dataIndex: 'issue_date',
      key: 'issue',
      render: (date: string) => dayjs(date).format('DD/MM/YYYY'),
    },
    {
      title: 'Vencimiento',
      dataIndex: 'expiration_date',
      key: 'expiration',
      render: (date: string) => dayjs(date).format('DD/MM/YYYY'),
    },
    {
      title: 'Estado',
      key: 'status',
      render: (_: any, record: UserCertification) => getStatusTag(record),
    },
  ];

  const tabItems = [
    {
      key: 'expiring',
      label: (
        <span>
          <WarningOutlined /> Por Vencer ({expiringCerts.length})
        </span>
      ),
      children: (
        <div>
          {expiringCerts.length > 0 ? (
            <>
              <Alert
                message="Certificaciones próximas a vencer"
                description="Las siguientes certificaciones vencen en los próximos 60 días."
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Table
                dataSource={expiringCerts}
                columns={allCertsColumns}
                rowKey="id"
                pagination={false}
              />
            </>
          ) : (
            <Alert
              message="Sin alertas"
              description="No hay certificaciones próximas a vencer en los próximos 60 días."
              type="success"
              showIcon
            />
          )}
        </div>
      ),
    },
    {
      key: 'byUser',
      label: (
        <span>
          <UserOutlined /> Por TAE
        </span>
      ),
      children: (
        <div>
          <div style={{ marginBottom: 16 }}>
            <Select
              placeholder="Selecciona un TAE"
              value={selectedUser}
              onChange={setSelectedUser}
              options={users.map((u) => ({ value: u.id, label: u.full_name }))}
              style={{ width: 300 }}
              allowClear
            />
          </div>
          {selectedUser ? (
            <Table
              dataSource={certifications}
              columns={userCertsColumns}
              rowKey="id"
              loading={loading}
              pagination={false}
            />
          ) : (
            <Text type="secondary">Selecciona un TAE para ver sus certificaciones</Text>
          )}
        </div>
      ),
    },
    {
      key: 'types',
      label: (
        <span>
          <SafetyCertificateOutlined /> Tipos
        </span>
      ),
      children: (
        <Table
          dataSource={certTypes}
          columns={[
            { title: 'Nombre', dataIndex: 'name', key: 'name' },
            { title: 'Descripción', dataIndex: 'description', key: 'desc' },
            { title: 'Vigencia', dataIndex: 'validity_months', key: 'validity', render: (v: number) => `${v} meses` },
            { title: 'Obligatoria', dataIndex: 'is_required', key: 'required', render: (v: boolean) => v ? <Tag color="red">Sí</Tag> : <Tag>No</Tag> },
          ]}
          rowKey="id"
          pagination={false}
        />
      ),
    },
  ];

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <Title level={4} style={{ margin: 0 }}>Gestión de Certificaciones</Title>
          {canManage && (
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
              Registrar Certificación
            </Button>
          )}
        </div>

        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
      </Card>

      {/* Modal crear certificación */}
      <Modal
        title="Registrar Certificación"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        okText="Registrar"
        width={500}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="user_id" label="TAE" rules={[{ required: true }]}>
            <Select
              placeholder="Selecciona TAE"
              options={users.map((u) => ({ value: u.id, label: u.full_name }))}
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            />
          </Form.Item>
          <Form.Item name="certification_type_id" label="Tipo de Certificación" rules={[{ required: true }]}>
            <Select
              placeholder="Selecciona tipo"
              options={certTypes.map((t) => ({ value: t.id, label: `${t.name} (${t.validity_months} meses)` }))}
            />
          </Form.Item>
          <Form.Item name="certificate_number" label="N° Certificado" rules={[{ required: true }]}>
            <Input placeholder="Ej: CERT-2024-001" />
          </Form.Item>
          <Form.Item name="issuing_entity" label="Entidad Emisora" rules={[{ required: true }]}>
            <Input placeholder="Ej: ARL Sura, Cruz Roja" />
          </Form.Item>
          <Form.Item name="issue_date" label="Fecha de Emisión" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Text type="secondary">
            La fecha de vencimiento se calculará automáticamente según la vigencia del tipo de certificación.
          </Text>
        </Form>
      </Modal>
    </div>
  );
};

export default CertificationsPage;
