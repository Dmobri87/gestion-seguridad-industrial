import { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Tag,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  message,
  Tabs,
  Badge,
  Collapse,
  List,
  Typography,
  Spin,
  ColorPicker,
  InputNumber,
  Switch,
  Popconfirm,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  FolderOutlined,
} from '@ant-design/icons';
import { activityApi } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

const { Title, Text } = Typography;
const { Panel } = Collapse;
const { TextArea } = Input;

interface Category {
  id: number;
  name: string;
  code: string;
  description: string;
  color: string;
  display_order: number;
  is_active: boolean;
}

interface Template {
  id: number;
  name: string;
  code: string;
  description: string;
  category_id: number;
  category_name?: string;
  default_frequency: number;
  requires_evidence: boolean;
  is_critical: boolean;
  is_active: boolean;
}

const ActivitiesPage = () => {
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState<Category[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [groupedTemplates, setGroupedTemplates] = useState<Record<string, Template[]>>({});
  const [activeTab, setActiveTab] = useState('templates');

  // Modals
  const [categoryModalOpen, setCategoryModalOpen] = useState(false);
  const [templateModalOpen, setTemplateModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role === 'Administrador';

  const [categoryForm] = Form.useForm();
  const [templateForm] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cats, temps] = await Promise.all([
        activityApi.getCategories(),
        activityApi.getTemplates(),
      ]);
      setCategories(cats);
      setTemplates(temps);

      // Agrupar templates por categoria
      const grouped: Record<string, Template[]> = {};
      temps.forEach((t: Template) => {
        const cat = cats.find((c: Category) => c.id === t.category_id);
        const catName = cat?.name || 'Sin Categoria';
        if (!grouped[catName]) grouped[catName] = [];
        grouped[catName].push({ ...t, category_name: catName });
      });
      setGroupedTemplates(grouped);
    } catch (error) {
      console.error('Error loading data:', error);
      message.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCategory = () => {
    setEditingCategory(null);
    categoryForm.resetFields();
    categoryForm.setFieldsValue({ color: '#1890ff', display_order: categories.length + 1 });
    setCategoryModalOpen(true);
  };

  const handleEditCategory = (cat: Category) => {
    setEditingCategory(cat);
    categoryForm.setFieldsValue(cat);
    setCategoryModalOpen(true);
  };

  const handleSaveCategory = async (values: any) => {
    try {
      const color = typeof values.color === 'string' ? values.color : values.color?.toHexString?.() || '#1890ff';
      const data = { ...values, color };

      if (editingCategory) {
        await activityApi.updateCategory(editingCategory.id, data);
        message.success('Categoría actualizada');
      } else {
        await activityApi.createCategory(data);
        message.success('Categoría creada');
      }
      setCategoryModalOpen(false);
      categoryForm.resetFields();
      setEditingCategory(null);
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al guardar categoría');
    }
  };

  const handleDeleteCategory = async (categoryId: number) => {
    try {
      await activityApi.deleteCategory(categoryId);
      message.success('Categoría desactivada');
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al eliminar');
    }
  };

  const handleCreateTemplate = () => {
    setEditingTemplate(null);
    templateForm.resetFields();
    templateForm.setFieldsValue({ default_frequency: 1, requires_evidence: false, is_critical: false });
    setTemplateModalOpen(true);
  };

  const handleEditTemplate = (template: Template) => {
    setEditingTemplate(template);
    templateForm.setFieldsValue(template);
    setTemplateModalOpen(true);
  };

  const handleSaveTemplate = async (values: any) => {
    try {
      if (editingTemplate) {
        await activityApi.updateTemplate(editingTemplate.id, values);
        message.success('Actividad actualizada');
      } else {
        await activityApi.createTemplate(values);
        message.success('Actividad creada');
      }
      setTemplateModalOpen(false);
      templateForm.resetFields();
      setEditingTemplate(null);
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al guardar actividad');
    }
  };

  const handleDeleteTemplate = async (templateId: number) => {
    try {
      await activityApi.deleteTemplate(templateId);
      message.success('Actividad desactivada');
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al eliminar');
    }
  };

  const categoryColumns = [
    {
      title: 'Color',
      dataIndex: 'color',
      key: 'color',
      width: 60,
      render: (color: string) => (
        <div style={{ width: 24, height: 24, borderRadius: 4, backgroundColor: color }} />
      ),
    },
    {
      title: 'Codigo',
      dataIndex: 'code',
      key: 'code',
      width: 100,
      render: (code: string, record: Category) => (
        <Tag color={record.color}>{code}</Tag>
      ),
    },
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Descripcion',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'Actividades',
      key: 'count',
      width: 100,
      render: (_: any, record: Category) => (
        <Badge count={templates.filter(t => t.category_id === record.id).length} showZero />
      ),
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>{active ? 'Activa' : 'Inactiva'}</Tag>
      ),
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 120,
      render: (_: any, record: Category) => (
        isAdmin ? (
          <Space size="small">
            <Tooltip title="Editar">
              <Button size="small" icon={<EditOutlined />} onClick={() => handleEditCategory(record)} />
            </Tooltip>
            <Popconfirm title="¿Desactivar esta categoría?" onConfirm={() => handleDeleteCategory(record.id)}>
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Space>
        ) : null
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

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <Title level={4} style={{ margin: 0, whiteSpace: 'nowrap', flexShrink: 0 }}>
          <AppstoreOutlined style={{ marginRight: 8 }} />
          Catalogo de Actividades
        </Title>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'templates',
            label: (
              <span>
                <UnorderedListOutlined />
                Plantillas de Actividades ({templates.length})
              </span>
            ),
            children: (
              <Card
                extra={
                  isAdmin && (
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateTemplate}>
                      Nueva Plantilla
                    </Button>
                  )
                }
              >
                {/* Vista agrupada por categoria */}
                <Collapse defaultActiveKey={Object.keys(groupedTemplates)}>
                  {Object.entries(groupedTemplates).map(([catName, temps]) => {
                    const cat = categories.find(c => c.name === catName);
                    return (
                      <Panel
                        key={catName}
                        header={
                          <Space>
                            <div
                              style={{
                                width: 16,
                                height: 16,
                                borderRadius: 4,
                                backgroundColor: cat?.color || '#1890ff',
                              }}
                            />
                            <Text strong>{catName}</Text>
                            <Badge count={temps.length} style={{ backgroundColor: cat?.color || '#1890ff' }} />
                          </Space>
                        }
                      >
                        <List
                          size="small"
                          dataSource={temps}
                          renderItem={(item) => (
                            <List.Item>
                              <div className="catalog-list-item-row">
                                <Tag className="catalog-list-item-fixed">{item.code}</Tag>
                                <div className="catalog-list-item-text">
                                  <div className="catalog-list-item-title">
                                    {item.name}
                                  </div>
                                  <Text type="secondary" className="catalog-list-item-description">
                                    {item.description}
                                  </Text>
                                </div>
                                <div className="catalog-list-item-fixed" style={{ display: 'flex', gap: 4 }}>
                                  {item.requires_evidence && <Tag color="blue">Evidencia</Tag>}
                                  {item.is_critical && <Tag color="red">Critica</Tag>}
                                  {isAdmin && (
                                    <>
                                      <Tooltip title="Editar">
                                        <Button
                                          type="text"
                                          size="small"
                                          icon={<EditOutlined />}
                                          onClick={() => handleEditTemplate(item)}
                                        />
                                      </Tooltip>
                                      <Popconfirm title="¿Desactivar?" onConfirm={() => handleDeleteTemplate(item.id)}>
                                        <Button type="text" size="small" danger icon={<DeleteOutlined />} />
                                      </Popconfirm>
                                    </>
                                  )}
                                </div>
                              </div>
                            </List.Item>
                          )}
                        />
                      </Panel>
                    );
                  })}
                </Collapse>
              </Card>
            ),
          },
          {
            key: 'categories',
            label: (
              <span>
                <FolderOutlined />
                Categorias ({categories.length})
              </span>
            ),
            children: (
              <Card
                extra={
                  isAdmin && (
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateCategory}>
                      Nueva Categoria
                    </Button>
                  )
                }
              >
                <Table
                  dataSource={categories}
                  columns={categoryColumns}
                  rowKey="id"
                  scroll={{ x: 500 }}
                  pagination={false}
                />
              </Card>
            ),
          },
        ]}
      />

      {/* Modal Categoria */}
      <Modal
        title={editingCategory ? 'Editar Categoria' : 'Nueva Categoria'}
        open={categoryModalOpen}
        onCancel={() => setCategoryModalOpen(false)}
        onOk={() => categoryForm.submit()}
        okText="Guardar"
        cancelText="Cancelar"
      >
        <Form form={categoryForm} layout="vertical" onFinish={handleSaveCategory}>
          <Form.Item name="name" label="Nombre" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="code" label="Código" rules={[{ required: true }]}>
            <Input placeholder="Ej: GRID, SOPORTE, ENTRENA" />
          </Form.Item>
          <Form.Item name="description" label="Descripción">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item name="color" label="Color">
            <ColorPicker format="hex" />
          </Form.Item>
          <Form.Item name="display_order" label="Orden">
            <InputNumber min={1} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal Template */}
      <Modal
        title={editingTemplate ? 'Editar Plantilla' : 'Nueva Plantilla'}
        open={templateModalOpen}
        onCancel={() => setTemplateModalOpen(false)}
        onOk={() => templateForm.submit()}
        okText="Guardar"
        cancelText="Cancelar"
        width={600}
      >
        <Form form={templateForm} layout="vertical" onFinish={handleSaveTemplate}>
          <Form.Item name="category_id" label="Categoría" rules={[{ required: true }]}>
            <Select
              options={categories.map(c => ({ value: c.id, label: c.name }))}
              placeholder="Seleccione categoría"
            />
          </Form.Item>
          <Form.Item name="name" label="Nombre" rules={[{ required: true }]}>
            <Input placeholder="Nombre de la actividad" />
          </Form.Item>
          <Form.Item name="code" label="Código" rules={[{ required: true }]}>
            <Input placeholder="Ej: GRID-MAQ, SOP-CHARLA" />
          </Form.Item>
          <Form.Item name="description" label="Descripción">
            <TextArea rows={3} placeholder="Descripción detallada de la actividad..." />
          </Form.Item>
          <Space size="large">
            <Form.Item name="default_frequency" label="Frecuencia por Ciclo">
              <InputNumber min={0} max={31} />
            </Form.Item>
            <Form.Item name="requires_evidence" label="Requiere Evidencia" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="is_critical" label="Es Critica" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </div>
  );
};

export default ActivitiesPage;
