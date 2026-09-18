import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Select, Space, Tag, Modal, Form, Input, message,
  Typography, Row, Col, Tabs, Badge, Avatar, Tooltip, Popconfirm, List,
  Divider, ColorPicker, Switch
} from 'antd';
import {
  PlusOutlined, UserOutlined, TeamOutlined, EditOutlined, DeleteOutlined,
  SettingOutlined, CrownOutlined, CheckCircleOutlined, StopOutlined,
  KeyOutlined, CopyOutlined, EyeOutlined
} from '@ant-design/icons';
import api, { usersApi, workGroupsApi } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

const { Title, Text } = Typography;

const ROLES = [
  { value: 'Administrador', label: 'Administrador', color: 'red' },
  { value: 'Supervisor', label: 'Supervisor', color: 'purple' },
  { value: 'Coordinador', label: 'Coordinador', color: 'blue' },
  { value: 'TAE', label: 'TAE', color: 'green' },
  { value: 'PSE', label: 'PSE', color: 'cyan' },
];

interface User {
  id: number;
  full_name: string;
  email: string;
  employee_code?: string;
  phone?: string;
  role: string;
  work_group_id?: number | null;
  is_active: boolean;
}

interface WorkGroup {
  id: number;
  name: string;
  code: string;
  color: string;
  description?: string;
  coordinator_id?: number | null;
  coordinator_name?: string;
  members_count?: number;
  members?: User[];
}

const AdminPage = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [presenceList, setPresenceList] = useState<any[]>([]);
  const [presenceLoading, setPresenceLoading] = useState(false);
  const [workGroups, setWorkGroups] = useState<WorkGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [groupModalOpen, setGroupModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [editingGroup, setEditingGroup] = useState<any>(null);
  const [selectedGroup, setSelectedGroup] = useState<WorkGroup | null>(null);
  const [groupDetailModal, setGroupDetailModal] = useState(false);
  const [filterRole, setFilterRole] = useState<string | undefined>(undefined);
  const [filterGroup, setFilterGroup] = useState<number | undefined>(undefined);
  const [resetPasswordModal, setResetPasswordModal] = useState(false);
  const [tempPassword, setTempPassword] = useState('');
  const [resetingUser, setResetingUser] = useState<User | null>(null);
  const [resetLoading, setResetLoading] = useState(false);
  const [userForm] = Form.useForm();
  const [groupForm] = Form.useForm();
  const currentUser = useAuthStore((state) => state.user);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const results = await Promise.allSettled([
        usersApi.getAll({ limit: 100 }),
        workGroupsApi.getAll(),
      ]);

      if (results[0].status === 'fulfilled') {
        setUsers(Array.isArray(results[0].value) ? results[0].value : []);
      } else {
        console.error('Error cargando usuarios:', results[0].reason);
        message.error('Error al cargar usuarios');
      }

      if (results[1].status === 'fulfilled') {
        setWorkGroups(Array.isArray(results[1].value) ? results[1].value : []);
      } else {
        console.error('Error cargando grupos:', results[1].reason);
        message.error('Error al cargar grupos de trabajo');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPresence = async () => {
    setPresenceLoading(true);
    try {
      const data = await usersApi.getPresenceList();
      setPresenceList(data);
    } catch (error) {
      console.error('Error loading presence:', error);
    } finally {
      setPresenceLoading(false);
    }
  };

  // ===== USUARIOS =====
  const handleCreateUser = async (values: any) => {
    try {
      if (editingUser) {
        const { password, email, ...updateData } = values;
        await usersApi.update(editingUser.id, updateData);
        message.success('Usuario actualizado');
      } else {
        await usersApi.create(values);
        message.success('Usuario creado exitosamente');
      }
      setUserModalOpen(false);
      userForm.resetFields();
      setEditingUser(null);
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error');
    }
  };

  const openEditUser = (user: any) => {
    setEditingUser(user);
    userForm.setFieldsValue({
      email: user.email,
      full_name: user.full_name,
      employee_code: user.employee_code,
      phone: user.phone,
      role: user.role,
      work_group_id: user.work_group_id,
      is_active: user.is_active,
    });
    setUserModalOpen(true);
  };

  const handleDeleteUser = async (userId: number) => {
    try {
      await usersApi.delete(userId);
      message.success('Usuario desactivado');
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error');
    }
  };

  const handleResetPassword = async (user: User) => {
    setResetingUser(user);
    setResetLoading(true);
    try {
      const response = await api.post(`/users/${user.id}/reset-password`);
      setTempPassword(response.data.temp_password);
      setResetPasswordModal(true);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al resetear contraseña');
    } finally {
      setResetLoading(false);
    }
  };

  // ===== GRUPOS =====
  const handleCreateGroup = async (values: any) => {
    try {
      const color = typeof values.color === 'string' ? values.color : values.color?.toHexString?.() || '#1890ff';
      const data = { ...values, color };

      if (editingGroup) {
        await workGroupsApi.update(editingGroup.id, data);
        message.success('Grupo actualizado');
      } else {
        await workGroupsApi.create(data);
        message.success('Grupo creado');
      }
      setGroupModalOpen(false);
      groupForm.resetFields();
      setEditingGroup(null);
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error');
    }
  };

  const openEditGroup = (group: any) => {
    setEditingGroup(group);
    groupForm.setFieldsValue({
      name: group.name,
      code: group.code,
      description: group.description,
      color: group.color,
      coordinator_id: group.coordinator_id,
    });
    setGroupModalOpen(true);
  };

  const openGroupDetail = async (group: any) => {
    try {
      const detail = await workGroupsApi.getById(group.id);
      setSelectedGroup(detail);
      setGroupDetailModal(true);
    } catch (error) {
      message.error('Error al cargar grupo');
    }
  };

  const handleRemoveMember = async (groupId: number, userId: number) => {
    try {
      await workGroupsApi.removeMember(groupId, userId);
      message.success('Miembro removido');
      const detail = await workGroupsApi.getById(groupId);
      setSelectedGroup(detail);
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error');
    }
  };

  const getRoleColor = (role: string) => {
    return ROLES.find(r => r.value === role)?.color || 'default';
  };

  const userColumns = [
    {
      title: 'Usuario',
      key: 'usuario',
      width: 180,
      ellipsis: true,
      render: (_: any, record: User) => (
        <div style={{ minWidth: 0 }}>
          <div style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {record.full_name}
          </div>
          <div style={{ fontSize: 12, color: '#888', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {record.email}
          </div>
        </div>
      ),
    },
    {
      title: 'Rol',
      dataIndex: 'role',
      key: 'role',
      width: 120,
      render: (role: string) => <Tag color={getRoleColor(role)}>{role}</Tag>,
    },
    {
      title: 'Grupo',
      key: 'group',
      width: 140,
      render: (_: any, record: User) => {
        const group = workGroups.find(g => g.id === record.work_group_id);
        return group ? (
          <Tag color={group.color}>{group.name}</Tag>
        ) : (
          <Text type="secondary">Sin grupo</Text>
        );
      },
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'active',
      width: 90,
      render: (active: boolean) => active
        ? <Tag color="success" icon={<CheckCircleOutlined />}>Activo</Tag>
        : <Tag color="error" icon={<StopOutlined />}>Inactivo</Tag>,
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 120,
      render: (_: any, record: any) => (
        <Space size="small">
          <Tooltip title="Editar">
            <Button size="small" icon={<EditOutlined />} onClick={() => openEditUser(record)} />
          </Tooltip>
          {record.id !== currentUser?.id && (
            <Tooltip title="Resetear contraseña">
              <Button
                size="small"
                icon={<KeyOutlined />}
                onClick={() => handleResetPassword(record)}
                loading={resetLoading && resetingUser?.id === record.id}
              />
            </Tooltip>
          )}
          {record.id !== currentUser?.id && (
            <Popconfirm title="¿Desactivar este usuario?" onConfirm={() => handleDeleteUser(record.id)}>
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <Title level={3} style={{ margin: 0, whiteSpace: 'nowrap', flexShrink: 0 }}>
            <SettingOutlined style={{ marginRight: 8 }} />
            Administración
          </Title>
          <Text type="secondary">Gestión de usuarios y grupos de trabajo</Text>
        </div>
      </div>

      <Tabs
        defaultActiveKey="users"
        onChange={(key) => { if (key === 'presence') loadPresence(); }}
        items={[
          {
            key: 'users',
            label: (
              <span>
                <UserOutlined />
                Usuarios <Badge count={users.length} style={{ marginLeft: 8, backgroundColor: '#1890ff' }} />
              </span>
            ),
            children: (
              <Card>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
                  <Select
                    placeholder="Filtrar por rol"
                    value={filterRole}
                    onChange={setFilterRole}
                    allowClear
                    style={{ minWidth: 150, flex: 1 }}
                    options={ROLES}
                  />
                  <Select
                    placeholder="Filtrar por grupo"
                    value={filterGroup}
                    onChange={setFilterGroup}
                    allowClear
                    style={{ minWidth: 150, flex: 1 }}
                    options={workGroups.map(g => ({ value: g.id, label: g.name }))}
                  />
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    style={{ flexShrink: 0 }}
                    onClick={() => {
                      setEditingUser(null);
                      userForm.resetFields();
                      setUserModalOpen(true);
                    }}
                  >
                    Nuevo Usuario
                  </Button>
                </div>
                <Table
                  dataSource={users ?? []}
                  columns={userColumns}
                  rowKey="id"
                  loading={loading}
                  scroll={{ x: 600 }}
                  pagination={{ pageSize: 15 }}
                  size="small"
                />
              </Card>
            ),
          },
          {
            key: 'groups',
            label: (
              <span>
                <TeamOutlined />
                Grupos de Trabajo <Badge count={workGroups.length} style={{ marginLeft: 8, backgroundColor: '#52c41a' }} />
              </span>
            ),
            children: (
              <Card>
                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => {
                      setEditingGroup(null);
                      groupForm.resetFields();
                      setGroupModalOpen(true);
                    }}
                  >
                    Nuevo Grupo
                  </Button>
                </div>
                <List
                  grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 3 }}
                  dataSource={workGroups}
                  renderItem={(group: WorkGroup) => (
                    <List.Item>
                      <Card
                        hoverable
                        style={{ borderTop: `4px solid ${group.color}` }}
                        actions={[
                          <Tooltip title="Ver miembros" key="view">
                            <Button type="link" icon={<TeamOutlined />} onClick={() => openGroupDetail(group)}>
                              {group.members_count} miembros
                            </Button>
                          </Tooltip>,
                          <Tooltip title="Editar" key="edit">
                            <Button type="link" icon={<EditOutlined />} onClick={() => openEditGroup(group)} />
                          </Tooltip>,
                        ]}
                      >
                        <Card.Meta
                          avatar={<Avatar style={{ backgroundColor: group.color }} size={48}>{group.code}</Avatar>}
                          title={group.name}
                          description={
                            <div>
                              {group.coordinator_name ? (
                                <Space>
                                  <CrownOutlined style={{ color: '#faad14' }} />
                                  <Text>{group.coordinator_name}</Text>
                                </Space>
                              ) : (
                                <Text type="secondary">Sin coordinador</Text>
                              )}
                              {group.description && (
                                <div style={{ marginTop: 4 }}>
                                  <Text type="secondary" style={{ fontSize: 12 }}>{group.description}</Text>
                                </div>
                              )}
                            </div>
                          }
                        />
                      </Card>
                    </List.Item>
                  )}
                />
              </Card>
            ),
          },
          {
            key: 'presence',
            label: (
              <span>
                <EyeOutlined />
                Presencia <Badge count={presenceList.filter((u: any) => u.is_online).length} style={{ marginLeft: 8, backgroundColor: '#10b981' }} />
              </span>
            ),
            children: (
              <Card>
                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text strong>Usuarios activos en la aplicacion</Text>
                  <Button size="small" onClick={loadPresence} loading={presenceLoading}>Actualizar</Button>
                </div>
                <Table
                  dataSource={presenceList}
                  rowKey="id"
                  loading={presenceLoading}
                  size="small"
                  pagination={false}
                  columns={[
                    {
                      title: 'Usuario',
                      dataIndex: 'full_name',
                      key: 'full_name',
                      render: (text: string, record: any) => (
                        <Space>
                          <Badge status={record.is_online ? 'success' : 'default'} />
                          <span>{text}</span>
                        </Space>
                      ),
                    },
                    { title: 'Email', dataIndex: 'email', key: 'email' },
                    {
                      title: 'Rol',
                      dataIndex: 'role',
                      key: 'role',
                      render: (role: string) => <Tag>{role}</Tag>,
                    },
                    {
                      title: 'Estado',
                      key: 'status',
                      render: (_: any, record: any) => (
                        <Tag color={record.is_online ? 'success' : 'default'}>
                          {record.is_online ? 'En linea' : 'Desconectado'}
                        </Tag>
                      ),
                    },
                    {
                      title: 'Modulo actual',
                      dataIndex: 'current_route',
                      key: 'current_route',
                      render: (route: string) => route ? <Tag color="blue">{route}</Tag> : '-',
                    },
                    {
                      title: 'Ultima actividad',
                      dataIndex: 'last_seen_at',
                      key: 'last_seen_at',
                      render: (date: string) => date ? new Date(date).toLocaleString('es-CO') : 'Nunca',
                    },
                  ]}
                />
              </Card>
            ),
          },
        ]}
      />

      {/* Modal Crear/Editar Usuario */}
      <Modal
        title={editingUser ? 'Editar Usuario' : 'Nuevo Usuario'}
        open={userModalOpen}
        onCancel={() => { setUserModalOpen(false); setEditingUser(null); userForm.resetFields(); }}
        onOk={() => userForm.submit()}
        okText={editingUser ? 'Guardar' : 'Crear'}
        cancelText="Cancelar"
        width={500}
      >
        <Form form={userForm} layout="vertical" onFinish={handleCreateUser}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="full_name" label="Nombre completo" rules={[{ required: true }]}>
                <Input placeholder="Nombre y Apellido" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="employee_code" label="Código empleado">
                <Input placeholder="TAE001" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
                <Input placeholder="email@empresa.com" disabled={!!editingUser} />
              </Form.Item>
            </Col>
            <Col span={12}>
              {!editingUser && (
                <Form.Item name="password" label="Contraseña" rules={[{ required: true, min: 6 }]}>
                  <Input.Password placeholder="Min. 6 caracteres" />
                </Form.Item>
              )}
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="role" label="Rol" rules={[{ required: true }]} initialValue="TAE">
                <Select options={ROLES} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="work_group_id" label="Grupo de Trabajo">
                <Select
                  placeholder="Seleccionar grupo"
                  allowClear
                  options={workGroups.map(g => ({ value: g.id, label: g.name }))}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="phone" label="Teléfono">
                <Input placeholder="+57 300 1234567" />
              </Form.Item>
            </Col>
            {editingUser && (
              <Col span={12}>
                <Form.Item name="is_active" label="Estado" valuePropName="checked">
                  <Switch checkedChildren="Activo" unCheckedChildren="Inactivo" />
                </Form.Item>
              </Col>
            )}
          </Row>
        </Form>
      </Modal>

      {/* Modal Crear/Editar Grupo */}
      <Modal
        title={editingGroup ? 'Editar Grupo' : 'Nuevo Grupo de Trabajo'}
        open={groupModalOpen}
        onCancel={() => { setGroupModalOpen(false); setEditingGroup(null); groupForm.resetFields(); }}
        onOk={() => groupForm.submit()}
        okText={editingGroup ? 'Guardar' : 'Crear'}
        cancelText="Cancelar"
        width={450}
      >
        <Form form={groupForm} layout="vertical" onFinish={handleCreateGroup}>
          <Row gutter={16}>
            <Col span={14}>
              <Form.Item name="name" label="Nombre del Grupo" rules={[{ required: true }]}>
                <Input placeholder="Ej: Jaguares" />
              </Form.Item>
            </Col>
            <Col span={10}>
              <Form.Item name="code" label="Código" rules={[{ required: true }]}>
                <Input placeholder="JAG" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="Descripción">
            <Input.TextArea rows={2} placeholder="Descripción del grupo..." />
          </Form.Item>
          <Row gutter={16}>
            <Col span={16}>
              <Form.Item name="coordinator_id" label="Coordinador">
                <Select
                  placeholder="Seleccionar coordinador"
                  allowClear
                  showSearch
                  optionFilterProp="label"
                  options={users
                    .filter(u => ['Administrador', 'Coordinador', 'Supervisor'].includes(u.role))
                    .map(u => ({ value: u.id, label: `${u.full_name} (${u.role})` }))
                  }
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="color" label="Color" initialValue="#1890ff">
                <ColorPicker format="hex" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Modal Detalle de Grupo */}
      <Modal
        title={
          selectedGroup ? (
            <Space>
              <Avatar style={{ backgroundColor: selectedGroup.color }}>{selectedGroup.code}</Avatar>
              <span>{selectedGroup.name}</span>
              <Badge count={selectedGroup.members_count} style={{ backgroundColor: selectedGroup.color }} />
            </Space>
          ) : 'Grupo'
        }
        open={groupDetailModal}
        onCancel={() => { setGroupDetailModal(false); setSelectedGroup(null); }}
        footer={null}
        width={500}
      >
        {selectedGroup && (
          <>
            {selectedGroup.coordinator_name && (
              <div style={{ marginBottom: 16 }}>
                <Space>
                  <CrownOutlined style={{ color: '#faad14' }} />
                  <Text strong>Coordinador:</Text>
                  <Text>{selectedGroup.coordinator_name}</Text>
                </Space>
              </div>
            )}
            <Divider>Miembros ({selectedGroup.members?.length || 0})</Divider>
            <List
              size="small"
              dataSource={selectedGroup.members || []}
              renderItem={(member: any) => (
                <List.Item
                  actions={[
                    <Popconfirm
                      key="rm"
                      title="¿Remover del grupo?"
                      onConfirm={() => handleRemoveMember(selectedGroup.id, member.id)}
                    >
                      <Button size="small" danger type="link">Remover</Button>
                    </Popconfirm>
                  ]}
                >
                  <List.Item.Meta
                    avatar={<Avatar icon={<UserOutlined />} size="small" />}
                    title={member.full_name}
                    description={
                      <Space>
                        <Tag color={getRoleColor(member.role)}>{member.role}</Tag>
                        <Text type="secondary">{member.employee_code}</Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
              locale={{ emptyText: 'Sin miembros asignados' }}
            />
          </>
        )}
      </Modal>
      {/* Modal Contraseña Temporal */}
      <Modal
        title={
          <Space>
            <KeyOutlined style={{ color: '#faad14' }} />
            Contraseña temporal generada
          </Space>
        }
        open={resetPasswordModal}
        onCancel={() => { setResetPasswordModal(false); setTempPassword(''); setResetingUser(null); }}
        footer={[
          <Button key="close" type="primary" onClick={() => { setResetPasswordModal(false); setTempPassword(''); setResetingUser(null); }}>
            Listo
          </Button>
        ]}
        width={420}
      >
        <div style={{ textAlign: 'center', padding: '16px 0' }}>
          <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
            Usuario: <Text strong>{resetingUser?.full_name}</Text>
          </Text>
          <Text type="secondary" style={{ display: 'block', marginBottom: 16, fontSize: 12 }}>
            Entrega esta contraseña temporal al usuario por WhatsApp o teléfono.
            Deberá cambiarla al ingresar.
          </Text>
          <div style={{
            background: '#f5f5f5',
            border: '1px dashed #d9d9d9',
            borderRadius: 8,
            padding: '16px 24px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            marginBottom: 16
          }}>
            <Text style={{ fontSize: 22, fontFamily: 'monospace', letterSpacing: 3, fontWeight: 600 }}>
              {tempPassword}
            </Text>
            <Tooltip title="Copiar">
              <Button
                type="text"
                icon={<CopyOutlined />}
                onClick={() => {
                  navigator.clipboard.writeText(tempPassword);
                  message.success('Copiado al portapapeles');
                }}
              />
            </Tooltip>
          </div>
          <div>
            <Text type="warning" style={{ fontSize: 12 }}>
              ⚠️ Esta contraseña solo se muestra una vez.
            </Text>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default AdminPage;
