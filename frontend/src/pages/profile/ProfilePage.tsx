import { useState } from 'react';
import {
  Card,
  Descriptions,
  Button,
  Form,
  Input,
  Typography,
  Row,
  Col,
  Avatar,
  Divider,
  Space,
  message,
  Tag,
  Modal,
} from 'antd';
import {
  UserOutlined,
  LockOutlined,
  EditOutlined,
  MailOutlined,
  PhoneOutlined,
  IdcardOutlined,
  SafetyCertificateOutlined,
  CalendarOutlined,
  SaveOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../../stores/authStore';
import { authApi } from '../../services/api';

const { Title, Text } = Typography;

const ROLE_COLORS: Record<string, string> = {
  Administrador: 'red',
  Coordinador: 'blue',
  Supervisor: 'purple',
  TAE: 'green',
  PSE: 'cyan',
  Empleado: 'default',
  Invitado: 'default',
};

const ProfilePage = () => {
  const { user, updateUser } = useAuthStore();
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [editForm] = Form.useForm();
  const [passwordForm] = Form.useForm();

  // --- Edit Profile ---
  const handleEditOpen = () => {
    editForm.setFieldsValue({
      full_name: user?.full_name || '',
      phone: user?.phone || '',
    });
    setEditModalOpen(true);
  };

  const handleEditSubmit = async () => {
    try {
      const values = await editForm.validateFields();
      setEditLoading(true);
      const updatedUser = await authApi.updateProfile(values);
      updateUser(updatedUser);
      message.success('Perfil actualizado correctamente');
      setEditModalOpen(false);
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      } else if (error?.errorFields) {
        // form validation error, do nothing
      } else {
        message.error('Error al actualizar el perfil');
      }
    } finally {
      setEditLoading(false);
    }
  };

  // --- Change Password ---
  const handlePasswordSubmit = async () => {
    try {
      const values = await passwordForm.validateFields();
      setPasswordLoading(true);
      await authApi.changePassword(values.current_password, values.new_password);
      message.success('Contrase\u00f1a actualizada correctamente');
      setPasswordModalOpen(false);
      passwordForm.resetFields();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      } else if (error?.errorFields) {
        // form validation error, do nothing
      } else {
        message.error('Error al cambiar la contrase\u00f1a');
      }
    } finally {
      setPasswordLoading(false);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (!user) {
    return null;
  }

  return (
    <div style={{ padding: '24px', maxWidth: 900, margin: '0 auto' }}>
      <Title level={3} style={{ marginBottom: 24 }}>
        <UserOutlined style={{ marginRight: 8 }} />
        Mi Perfil
      </Title>

      {/* User Info Card */}
      <Card
        style={{ marginBottom: 24 }}
        bodyStyle={{ padding: 0 }}
      >
        {/* Header with avatar and basic info */}
        <div
          style={{
            background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
            padding: '32px 24px',
            display: 'flex',
            alignItems: 'center',
            gap: 24,
            borderRadius: '8px 8px 0 0',
          }}
        >
          <Avatar
            size={80}
            icon={<UserOutlined />}
            style={{
              backgroundColor: 'rgba(255,255,255,0.2)',
              border: '3px solid rgba(255,255,255,0.5)',
              fontSize: 36,
            }}
          />
          <div>
            <Title level={4} style={{ color: '#fff', margin: 0 }}>
              {user.full_name}
            </Title>
            <Text style={{ color: 'rgba(255,255,255,0.85)', display: 'block', marginTop: 4 }}>
              {user.email}
            </Text>
            <Tag
              color={ROLE_COLORS[user.role] || 'default'}
              style={{ marginTop: 8 }}
            >
              {user.role}
            </Tag>
          </div>
        </div>

        {/* Details */}
        <div style={{ padding: '24px' }}>
          <Descriptions
            column={{ xs: 1, sm: 2 }}
            labelStyle={{ fontWeight: 600, color: '#595959' }}
            contentStyle={{ color: '#262626' }}
          >
            <Descriptions.Item
              label={
                <Space>
                  <MailOutlined />
                  {'Correo electr\u00f3nico'}
                </Space>
              }
            >
              {user.email}
            </Descriptions.Item>
            <Descriptions.Item
              label={
                <Space>
                  <PhoneOutlined />
                  {'Tel\u00e9fono'}
                </Space>
              }
            >
              {user.phone || 'No registrado'}
            </Descriptions.Item>
            <Descriptions.Item
              label={
                <Space>
                  <IdcardOutlined />
                  {'C\u00f3digo de empleado'}
                </Space>
              }
            >
              {user.employee_code || 'No asignado'}
            </Descriptions.Item>
            <Descriptions.Item
              label={
                <Space>
                  <SafetyCertificateOutlined />
                  Rol
                </Space>
              }
            >
              <Tag color={ROLE_COLORS[user.role] || 'default'}>{user.role}</Tag>
            </Descriptions.Item>
            <Descriptions.Item
              label={
                <Space>
                  <CalendarOutlined />
                  Miembro desde
                </Space>
              }
            >
              {formatDate(user.created_at)}
            </Descriptions.Item>
            <Descriptions.Item
              label={
                <Space>
                  <UserOutlined />
                  Estado
                </Space>
              }
            >
              <Tag color={user.is_active ? 'green' : 'red'}>
                {user.is_active ? 'Activo' : 'Inactivo'}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        </div>
      </Card>

      {/* Action Buttons */}
      <Row gutter={16}>
        <Col xs={24} sm={12}>
          <Card
            hoverable
            style={{ marginBottom: 16, textAlign: 'center' }}
            onClick={handleEditOpen}
          >
            <EditOutlined style={{ fontSize: 32, color: '#1890ff', marginBottom: 12 }} />
            <Title level={5} style={{ margin: 0 }}>Editar Perfil</Title>
            <Text type="secondary">{'Actualizar nombre y tel\u00e9fono'}</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card
            hoverable
            style={{ marginBottom: 16, textAlign: 'center' }}
            onClick={() => {
              passwordForm.resetFields();
              setPasswordModalOpen(true);
            }}
          >
            <LockOutlined style={{ fontSize: 32, color: '#faad14', marginBottom: 12 }} />
            <Title level={5} style={{ margin: 0 }}>{'Cambiar Contrase\u00f1a'}</Title>
            <Text type="secondary">{'Actualizar contrase\u00f1a de acceso'}</Text>
          </Card>
        </Col>
      </Row>

      {/* Edit Profile Modal */}
      <Modal
        title={
          <Space>
            <EditOutlined />
            Editar Perfil
          </Space>
        }
        open={editModalOpen}
        onCancel={() => setEditModalOpen(false)}
        footer={[
          <Button key="cancel" icon={<CloseOutlined />} onClick={() => setEditModalOpen(false)}>
            Cancelar
          </Button>,
          <Button
            key="save"
            type="primary"
            icon={<SaveOutlined />}
            loading={editLoading}
            onClick={handleEditSubmit}
          >
            Guardar Cambios
          </Button>,
        ]}
        destroyOnClose
      >
        <Divider style={{ margin: '12px 0 24px' }} />
        <Form
          form={editForm}
          layout="vertical"
        >
          <Form.Item
            name="full_name"
            label="Nombre completo"
            rules={[
              { required: true, message: 'El nombre es obligatorio' },
              { min: 3, message: 'El nombre debe tener al menos 3 caracteres' },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Ingrese su nombre completo"
              maxLength={255}
            />
          </Form.Item>
          <Form.Item
            name="phone"
            label={'Tel\u00e9fono'}
            rules={[
              { max: 50, message: 'El tel\u00e9fono no puede exceder 50 caracteres' },
            ]}
          >
            <Input
              prefix={<PhoneOutlined />}
              placeholder={'Ingrese su n\u00famero de tel\u00e9fono'}
              maxLength={50}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Change Password Modal */}
      <Modal
        title={
          <Space>
            <LockOutlined />
            {'Cambiar Contrase\u00f1a'}
          </Space>
        }
        open={passwordModalOpen}
        onCancel={() => setPasswordModalOpen(false)}
        footer={[
          <Button key="cancel" icon={<CloseOutlined />} onClick={() => setPasswordModalOpen(false)}>
            Cancelar
          </Button>,
          <Button
            key="save"
            type="primary"
            icon={<SaveOutlined />}
            loading={passwordLoading}
            onClick={handlePasswordSubmit}
          >
            {'Cambiar Contrase\u00f1a'}
          </Button>,
        ]}
        destroyOnClose
      >
        <Divider style={{ margin: '12px 0 24px' }} />
        <Form
          form={passwordForm}
          layout="vertical"
        >
          <Form.Item
            name="current_password"
            label={'Contrase\u00f1a actual'}
            rules={[
              { required: true, message: 'Ingrese su contrase\u00f1a actual' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder={'Ingrese su contrase\u00f1a actual'}
            />
          </Form.Item>
          <Form.Item
            name="new_password"
            label={'Nueva contrase\u00f1a'}
            rules={[
              { required: true, message: 'Ingrese la nueva contrase\u00f1a' },
              { min: 8, message: 'La contrase\u00f1a debe tener al menos 8 caracteres' },
              {
                pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
                message: 'Debe contener may\u00fascula, min\u00fascula y n\u00famero',
              },
            ]}
            hasFeedback
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder={'Ingrese la nueva contrase\u00f1a'}
            />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label={'Confirmar nueva contrase\u00f1a'}
            dependencies={['new_password']}
            hasFeedback
            rules={[
              { required: true, message: 'Confirme la nueva contrase\u00f1a' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Las contrase\u00f1as no coinciden'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder={'Confirme la nueva contrase\u00f1a'}
            />
          </Form.Item>
          <div
            style={{
              background: '#f6f8fa',
              borderRadius: 6,
              padding: '12px 16px',
              fontSize: 13,
              color: '#595959',
            }}
          >
            <Text strong style={{ display: 'block', marginBottom: 4 }}>
              {'Requisitos de contrase\u00f1a:'}
            </Text>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>{'M\u00ednimo 8 caracteres'}</li>
              <li>{'Al menos una letra may\u00fascula'}</li>
              <li>{'Al menos una letra min\u00fascula'}</li>
              <li>{'Al menos un n\u00famero'}</li>
            </ul>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default ProfilePage;
