import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Select, Space, Tag, Modal, Form, Input, message,
  Typography, DatePicker, Row, Col, Statistic, Progress, Tabs, Badge,
  List, Empty, Tooltip, Divider, Upload, Image
} from 'antd';
import {
  PlusOutlined, CheckOutlined, CloseOutlined, ClockCircleOutlined,
  CalendarOutlined, FireOutlined, FileTextOutlined, CheckCircleOutlined,
  ExclamationCircleOutlined, SyncOutlined, UploadOutlined, PaperClipOutlined,
  EyeOutlined, DeleteOutlined, CameraOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { executionsApi } from '../../services/api';
import type { ActivityExecution } from '../../types';
import { useAuthStore } from '../../stores/authStore';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface PendingActivity {
  planned_activity_id: number;
  activity_name: string;
  activity_code: string;
  total_planned: number;
  total_executed: number;
  pending: number;
  compliance_percentage: number;
  requires_evidence: boolean;
}

interface ExecutionStats {
  total_executions: number;
  completed: number;
  pending: number;
  with_novelty: number;
  pending_approval: number;
  approved: number;
  rejected: number;
}

interface EvidenceFile {
  id: number;
  execution_id: number;
  file_name: string;
  file_type: string;
  file_size?: number;
  file_url: string;
  description?: string;
  is_primary: boolean;
  created_at: string;
  uploaded_by: number;
}

const ExecutionPage = () => {
  const [loading, setLoading] = useState(true);
  const [executions, setExecutions] = useState<ActivityExecution[]>([]);
  const [pendingActivities, setPendingActivities] = useState<PendingActivity[]>([]);
  const [stats, setStats] = useState<ExecutionStats | null>(null);
  const [year, setYear] = useState(dayjs().year());
  const [month, setMonth] = useState(dayjs().month() + 1);
  const [modalOpen, setModalOpen] = useState(false);
  const [quickModalOpen, setQuickModalOpen] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState<PendingActivity | null>(null);
  const [form] = Form.useForm();
  const [quickForm] = Form.useForm();
  const user = useAuthStore((state) => state.user);

  // Estado para evidencias
  const [fileList, setFileList] = useState<any[]>([]);
  const [quickFileList, setQuickFileList] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);

  // Estado para modal de ver evidencias
  const [evidenceModalOpen, setEvidenceModalOpen] = useState(false);
  const [evidenceFiles, setEvidenceFiles] = useState<EvidenceFile[]>([]);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [selectedExecutionId, setSelectedExecutionId] = useState<number | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewImage, setPreviewImage] = useState('');

  const isApprover = ['Administrador', 'Coordinador', 'Supervisor'].includes(user?.role || '');

  useEffect(() => {
    loadData();
  }, [year, month]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [execsResponse, pendingResponse, statsResponse] = await Promise.all([
        executionsApi.getAll(year, month),
        executionsApi.getMyToday(),
        executionsApi.getStats(year, month),
      ]);
      setExecutions(execsResponse);
      setPendingActivities(pendingResponse.activities || []);
      setStats(statsResponse);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  // ==========================================
  // UPLOAD DE EVIDENCIAS POST-CREACIÓN
  // ==========================================

  const uploadFilesToExecution = async (executionId: number, files: any[]) => {
    if (files.length === 0) return;
    setUploading(true);
    let uploaded = 0;
    for (const fileItem of files) {
      try {
        await executionsApi.uploadFile(executionId, fileItem.originFileObj || fileItem);
        uploaded++;
      } catch (error) {
        console.error('Error uploading file:', error);
      }
    }
    setUploading(false);
    if (uploaded > 0) {
      message.success(`${uploaded} evidencia${uploaded > 1 ? 's' : ''} adjuntada${uploaded > 1 ? 's' : ''}`);
    }
  };

  const handleCreateExecution = async (values: any) => {
    try {
      const cycleNumber = Math.ceil(dayjs(values.execution_date).date() / 7);

      const result = await executionsApi.create({
        planned_activity_id: values.planned_activity_id,
        user_id: user?.id,
        organization_id: user?.organization_id,
        execution_date: values.execution_date.format('YYYY-MM-DD'),
        cycle_number: Math.min(cycleNumber, 4),
        status: values.status,
        observation: values.observation,
        quantity: values.quantity || 1,
      });

      // Subir evidencias si hay
      if (fileList.length > 0) {
        await uploadFilesToExecution(result.id, fileList);
      }

      message.success('Ejecución registrada exitosamente');
      setModalOpen(false);
      form.resetFields();
      setFileList([]);
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al registrar la ejecución');
    }
  };

  const handleQuickExecution = async (values: any) => {
    if (!selectedActivity) return;

    try {
      const cycleNumber = Math.ceil(dayjs().date() / 7);

      const result = await executionsApi.create({
        planned_activity_id: selectedActivity.planned_activity_id,
        user_id: user?.id,
        organization_id: user?.organization_id,
        execution_date: dayjs().format('YYYY-MM-DD'),
        cycle_number: Math.min(cycleNumber, 4),
        status: values.status || 'Completado',
        observation: values.observation,
        quantity: 1,
      });

      // Subir evidencias si hay
      if (quickFileList.length > 0) {
        await uploadFilesToExecution(result.id, quickFileList);
      }

      message.success(`${selectedActivity.activity_name} registrada`);
      setQuickModalOpen(false);
      quickForm.resetFields();
      setQuickFileList([]);
      setSelectedActivity(null);
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al registrar');
    }
  };

  const handleApprove = async (executionId: number, approved: boolean) => {
    try {
      await executionsApi.approve(executionId, approved);
      message.success(approved ? 'Ejecución aprobada' : 'Ejecución rechazada');
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error en la operación');
    }
  };

  // ==========================================
  // VER EVIDENCIAS
  // ==========================================

  const openEvidenceModal = async (executionId: number) => {
    setSelectedExecutionId(executionId);
    setEvidenceModalOpen(true);
    setEvidenceLoading(true);
    try {
      const files = await executionsApi.getFiles(executionId);
      setEvidenceFiles(files);
    } catch (error) {
      console.error('Error loading files:', error);
      setEvidenceFiles([]);
    } finally {
      setEvidenceLoading(false);
    }
  };

  const handleDeleteFile = async (fileId: number) => {
    if (!selectedExecutionId) return;
    try {
      await executionsApi.deleteFile(selectedExecutionId, fileId);
      message.success('Archivo eliminado');
      setEvidenceFiles(evidenceFiles.filter(f => f.id !== fileId));
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al eliminar');
    }
  };

  const handleUploadToExisting = async (file: any) => {
    if (!selectedExecutionId) return false;
    try {
      const newFile = await executionsApi.uploadFile(selectedExecutionId, file);
      setEvidenceFiles(prev => [newFile, ...prev]);
      message.success('Evidencia adjuntada');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al subir archivo');
    }
    return false;
  };

  const isImageFile = (fileType: string) => fileType.startsWith('image/');

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const openQuickModal = (activity: PendingActivity) => {
    setSelectedActivity(activity);
    setQuickModalOpen(true);
  };

  const getStatusTag = (status: string) => {
    const config: Record<string, { color: string; icon: React.ReactNode }> = {
      'Completado': { color: 'green', icon: <CheckCircleOutlined /> },
      'Pendiente': { color: 'orange', icon: <ClockCircleOutlined /> },
      'Con Novedad': { color: 'red', icon: <ExclamationCircleOutlined /> },
    };
    const { color, icon } = config[status] || { color: 'default', icon: null };
    return <Tag color={color} icon={icon}>{status}</Tag>;
  };

  const getApprovalTag = (status: string) => {
    const config: Record<string, { color: string; icon: React.ReactNode }> = {
      'Pendiente': { color: 'processing', icon: <SyncOutlined spin /> },
      'Aprobado': { color: 'success', icon: <CheckOutlined /> },
      'Rechazado': { color: 'error', icon: <CloseOutlined /> },
    };
    const { color, icon } = config[status] || { color: 'default', icon: null };
    return <Tag color={color} icon={icon}>{status}</Tag>;
  };

  const columns = [
    {
      title: 'Fecha',
      dataIndex: 'execution_date',
      key: 'date',
      width: 100,
      render: (date: string) => dayjs(date).format('DD/MM/YY'),
    },
    {
      title: 'Actividad',
      dataIndex: 'activity_name',
      key: 'activity',
      ellipsis: true,
    },
    {
      title: 'TAE',
      dataIndex: 'user_name',
      key: 'user',
      width: 150,
      ellipsis: true,
    },
    {
      title: 'Ciclo',
      dataIndex: 'cycle_number',
      key: 'cycle',
      width: 70,
      align: 'center' as const,
      render: (cycle: number) => <Tag>C{cycle}</Tag>,
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: 'Aprobación',
      dataIndex: 'approval_status',
      key: 'approval',
      width: 120,
      render: (status: string) => getApprovalTag(status),
    },
    {
      title: 'Evidencias',
      dataIndex: 'files_count',
      key: 'files',
      width: 100,
      align: 'center' as const,
      render: (count: number, record: ActivityExecution) => (
        <Button
          type="link"
          size="small"
          icon={<PaperClipOutlined />}
          onClick={() => openEvidenceModal(record.id)}
        >
          {count || 0}
        </Button>
      ),
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 120,
      render: (_: any, record: ActivityExecution) => (
        <Space size="small">
          {isApprover && record.approval_status === 'Pendiente' && (
            <>
              <Tooltip title="Aprobar">
                <Button
                  type="primary"
                  size="small"
                  icon={<CheckOutlined />}
                  onClick={() => handleApprove(record.id, true)}
                />
              </Tooltip>
              <Tooltip title="Rechazar">
                <Button
                  danger
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => handleApprove(record.id, false)}
                />
              </Tooltip>
            </>
          )}
        </Space>
      ),
    },
  ];

  const months = [
    { value: 1, label: 'Enero' }, { value: 2, label: 'Febrero' }, { value: 3, label: 'Marzo' },
    { value: 4, label: 'Abril' }, { value: 5, label: 'Mayo' }, { value: 6, label: 'Junio' },
    { value: 7, label: 'Julio' }, { value: 8, label: 'Agosto' }, { value: 9, label: 'Septiembre' },
    { value: 10, label: 'Octubre' }, { value: 11, label: 'Noviembre' }, { value: 12, label: 'Diciembre' },
  ];

  const totalPending = pendingActivities.reduce((sum, a) => sum + a.pending, 0);

  const uploadProps = {
    multiple: true,
    accept: 'image/*,.pdf,.doc,.docx,.xls,.xlsx,.mp4,.mov,.avi',
    beforeUpload: () => false,
    listType: 'picture' as const,
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>
            <CalendarOutlined style={{ marginRight: 8 }} />
            Registro de Ejecuciones
          </Title>
          <Text type="secondary">Gestiona y registra las actividades ejecutadas</Text>
        </div>
        <Space>
          <Select value={month} onChange={setMonth} options={months} style={{ width: 140 }} />
          <Select
            value={year}
            onChange={setYear}
            options={[{ value: 2024, label: '2024' }, { value: 2025, label: '2025' }, { value: 2026, label: '2026' }]}
            style={{ width: 100 }}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            Nueva Ejecución
          </Button>
        </Space>
      </div>

      {/* Estadísticas */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col xs={12} sm={6} lg={4}>
            <Card size="small">
              <Statistic title="Total Ejecutadas" value={stats.total_executions} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#1890ff' }} />
            </Card>
          </Col>
          <Col xs={12} sm={6} lg={4}>
            <Card size="small">
              <Statistic title="Completadas" value={stats.completed} prefix={<CheckOutlined />} valueStyle={{ color: '#52c41a' }} />
            </Card>
          </Col>
          <Col xs={12} sm={6} lg={4}>
            <Card size="small">
              <Statistic title="Con Novedad" value={stats.with_novelty} prefix={<ExclamationCircleOutlined />} valueStyle={{ color: '#ff4d4f' }} />
            </Card>
          </Col>
          <Col xs={12} sm={6} lg={4}>
            <Card size="small">
              <Statistic title="Por Aprobar" value={stats.pending_approval} prefix={<ClockCircleOutlined />} valueStyle={{ color: '#faad14' }} />
            </Card>
          </Col>
          <Col xs={12} sm={6} lg={4}>
            <Card size="small">
              <Statistic title="Aprobadas" value={stats.approved} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#52c41a' }} />
            </Card>
          </Col>
          <Col xs={12} sm={6} lg={4}>
            <Card size="small">
              <Statistic title="Rechazadas" value={stats.rejected} prefix={<CloseOutlined />} valueStyle={{ color: '#ff4d4f' }} />
            </Card>
          </Col>
        </Row>
      )}

      <Tabs
        defaultActiveKey="pending"
        items={[
          {
            key: 'pending',
            label: <span><FireOutlined /> Mis Pendientes <Badge count={totalPending} style={{ marginLeft: 8 }} /></span>,
            children: (
              <Card>
                {pendingActivities.length > 0 ? (
                  <List
                    grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4 }}
                    dataSource={pendingActivities}
                    renderItem={(item) => (
                      <List.Item>
                        <Card
                          size="small"
                          hoverable
                          onClick={() => openQuickModal(item)}
                          style={{ cursor: 'pointer' }}
                          actions={[
                            <Button type="primary" size="small" icon={<CheckOutlined />}
                              onClick={(e) => { e.stopPropagation(); openQuickModal(item); }}>
                              Registrar
                            </Button>
                          ]}
                        >
                          <Card.Meta
                            title={
                              <Space>
                                <Tag color="blue">{item.activity_code}</Tag>
                                {item.requires_evidence && (
                                  <Tooltip title="Requiere evidencia">
                                    <CameraOutlined style={{ color: '#faad14' }} />
                                  </Tooltip>
                                )}
                              </Space>
                            }
                            description={
                              <div>
                                <Text ellipsis style={{ display: 'block', marginBottom: 8 }}>{item.activity_name}</Text>
                                <Progress percent={item.compliance_percentage} size="small"
                                  format={() => `${item.total_executed}/${item.total_planned}`} />
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  Pendientes: <Text strong style={{ color: '#ff4d4f' }}>{item.pending}</Text>
                                </Text>
                              </div>
                            }
                          />
                        </Card>
                      </List.Item>
                    )}
                  />
                ) : (
                  <Empty description="No tienes actividades pendientes para este mes" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                )}
              </Card>
            ),
          },
          {
            key: 'history',
            label: <span><CalendarOutlined /> Historial <Badge count={executions.length} style={{ marginLeft: 8, backgroundColor: '#1890ff' }} /></span>,
            children: (
              <Card>
                <Table dataSource={executions} columns={columns} rowKey="id" loading={loading}
                  pagination={{ defaultPageSize: 15, showSizeChanger: true, pageSizeOptions: ['15', '20', '50', '100'] }} size="small" />
              </Card>
            ),
          },
          {
            key: 'approval',
            label: <span><CheckCircleOutlined /> Por Aprobar <Badge count={stats?.pending_approval || 0} style={{ marginLeft: 8, backgroundColor: '#faad14' }} /></span>,
            disabled: !isApprover,
            children: (
              <Card>
                <Table dataSource={executions.filter(e => e.approval_status === 'Pendiente')} columns={columns}
                  rowKey="id" loading={loading} pagination={{ defaultPageSize: 15, showSizeChanger: true, pageSizeOptions: ['15', '20', '50', '100'] }} size="small"
                  locale={{ emptyText: 'No hay ejecuciones pendientes de aprobación' }} />
              </Card>
            ),
          },
        ]}
      />

      {/* ===== MODAL NUEVA EJECUCIÓN ===== */}
      <Modal
        title={<Space><PlusOutlined /><span>Registrar Nueva Ejecución</span></Space>}
        open={modalOpen}
        onCancel={() => { setModalOpen(false); setFileList([]); }}
        onOk={() => form.submit()}
        okText={uploading ? 'Subiendo...' : 'Registrar'}
        okButtonProps={{ loading: uploading }}
        cancelText="Cancelar"
        width={550}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateExecution}>
          <Form.Item name="planned_activity_id" label="Actividad"
            rules={[{ required: true, message: 'Selecciona una actividad' }]}>
            <Select placeholder="Selecciona la actividad a registrar" showSearch optionFilterProp="label"
              options={pendingActivities.map((a) => ({
                value: a.planned_activity_id,
                label: `${a.activity_code} - ${a.activity_name} (Pendiente: ${a.pending})`,
              }))} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="execution_date" label="Fecha de Ejecución" rules={[{ required: true }]} initialValue={dayjs()}>
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="quantity" label="Cantidad" initialValue={1}>
                <Select options={[
                  { value: 1, label: '1' }, { value: 2, label: '2' }, { value: 3, label: '3' },
                  { value: 4, label: '4' }, { value: 5, label: '5' },
                ]} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="status" label="Estado" rules={[{ required: true }]} initialValue="Completado">
            <Select options={[
              { value: 'Completado', label: 'Completado' },
              { value: 'Pendiente', label: 'Pendiente' },
              { value: 'Con Novedad', label: 'Con Novedad' },
            ]} />
          </Form.Item>
          <Form.Item name="observation" label="Observación">
            <TextArea rows={2} placeholder="Agrega observaciones o comentarios..." />
          </Form.Item>
          <Divider style={{ margin: '12px 0' }} />
          <Form.Item label={<Space><CameraOutlined /><span>Evidencias (fotos, documentos)</span></Space>}>
            <Upload {...uploadProps} fileList={fileList} onChange={({ fileList: fl }) => setFileList(fl)}>
              <Button icon={<UploadOutlined />}>Adjuntar Evidencia</Button>
            </Upload>
            <Text type="secondary" style={{ fontSize: 11 }}>
              Máx. 10MB por archivo. Formatos: imágenes, PDF, documentos Office, videos.
            </Text>
          </Form.Item>
        </Form>
      </Modal>

      {/* ===== MODAL REGISTRO RÁPIDO ===== */}
      <Modal
        title={<Space><CheckOutlined style={{ color: '#52c41a' }} /><span>Registro Rápido</span></Space>}
        open={quickModalOpen}
        onCancel={() => { setQuickModalOpen(false); setSelectedActivity(null); quickForm.resetFields(); setQuickFileList([]); }}
        onOk={() => quickForm.submit()}
        okText={uploading ? 'Subiendo...' : 'Registrar'}
        okButtonProps={{ loading: uploading }}
        cancelText="Cancelar"
        width={450}
      >
        {selectedActivity && (
          <>
            <Card size="small" style={{ marginBottom: 16, backgroundColor: '#f5f5f5' }}>
              <Space direction="vertical" size={0}>
                <Text strong>{selectedActivity.activity_name}</Text>
                <Text type="secondary">Código: {selectedActivity.activity_code}</Text>
                <Divider style={{ margin: '8px 0' }} />
                <Row gutter={16}>
                  <Col span={8}>
                    <Text type="secondary">Planeado</Text>
                    <div><Text strong>{selectedActivity.total_planned}</Text></div>
                  </Col>
                  <Col span={8}>
                    <Text type="secondary">Ejecutado</Text>
                    <div><Text strong style={{ color: '#52c41a' }}>{selectedActivity.total_executed}</Text></div>
                  </Col>
                  <Col span={8}>
                    <Text type="secondary">Pendiente</Text>
                    <div><Text strong style={{ color: '#ff4d4f' }}>{selectedActivity.pending}</Text></div>
                  </Col>
                </Row>
              </Space>
            </Card>

            <Form form={quickForm} layout="vertical" onFinish={handleQuickExecution}>
              <Form.Item name="status" label="Estado" initialValue="Completado">
                <Select options={[
                  { value: 'Completado', label: 'Completado' },
                  { value: 'Con Novedad', label: 'Con Novedad' },
                ]} />
              </Form.Item>
              <Form.Item name="observation" label="Observación (opcional)">
                <TextArea rows={2} placeholder="Agrega una observación..." />
              </Form.Item>
              <Form.Item label={
                <Space>
                  <CameraOutlined />
                  <span>Evidencias</span>
                  {selectedActivity.requires_evidence && <Tag color="warning">Requerida</Tag>}
                </Space>
              }>
                <Upload {...uploadProps} fileList={quickFileList} onChange={({ fileList: fl }) => setQuickFileList(fl)}>
                  <Button icon={<UploadOutlined />}>Adjuntar Evidencia</Button>
                </Upload>
              </Form.Item>
            </Form>
          </>
        )}
      </Modal>

      {/* ===== MODAL VER EVIDENCIAS ===== */}
      <Modal
        title={<Space><PaperClipOutlined /><span>Evidencias Adjuntas</span></Space>}
        open={evidenceModalOpen}
        onCancel={() => { setEvidenceModalOpen(false); setEvidenceFiles([]); setSelectedExecutionId(null); }}
        footer={null}
        width={600}
      >
        <div style={{ marginBottom: 16 }}>
          <Upload accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.mp4,.mov,.avi"
            showUploadList={false} beforeUpload={handleUploadToExisting}>
            <Button icon={<UploadOutlined />} size="small">Agregar Evidencia</Button>
          </Upload>
        </div>

        {evidenceLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>Cargando...</div>
        ) : evidenceFiles.length === 0 ? (
          <Empty description="Sin evidencias adjuntas" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <List
            dataSource={evidenceFiles}
            renderItem={(file) => (
              <List.Item
                actions={[
                  isImageFile(file.file_type) ? (
                    <Tooltip title="Ver imagen" key="preview">
                      <Button type="link" size="small" icon={<EyeOutlined />}
                        onClick={() => { setPreviewImage(file.file_url); setPreviewOpen(true); }} />
                    </Tooltip>
                  ) : null,
                  <Tooltip title="Descargar" key="download">
                    <Button type="link" size="small" icon={<FileTextOutlined />}
                      onClick={() => window.open(file.file_url, '_blank')} />
                  </Tooltip>,
                  <Tooltip title="Eliminar" key="delete">
                    <Button type="link" danger size="small" icon={<DeleteOutlined />}
                      onClick={() => handleDeleteFile(file.id)} />
                  </Tooltip>,
                ].filter(Boolean)}
              >
                <List.Item.Meta
                  avatar={
                    isImageFile(file.file_type) ? (
                      <Image src={file.file_url} width={48} height={48}
                        style={{ objectFit: 'cover', borderRadius: 4 }} preview={false}
                        fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mN88P/BfwAJhAPjM9uBIwAAAABJRU5ErkJggg==" />
                    ) : (
                      <div style={{ width: 48, height: 48, display: 'flex', alignItems: 'center',
                        justifyContent: 'center', background: '#f0f0f0', borderRadius: 4 }}>
                        <FileTextOutlined style={{ fontSize: 24, color: '#999' }} />
                      </div>
                    )
                  }
                  title={file.file_name}
                  description={
                    <Space>
                      <Text type="secondary" style={{ fontSize: 12 }}>{formatFileSize(file.file_size)}</Text>
                      <Text type="secondary" style={{ fontSize: 12 }}>{dayjs(file.created_at).format('DD/MM/YY HH:mm')}</Text>
                      {file.is_primary && <Tag color="blue" style={{ fontSize: 10 }}>Principal</Tag>}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Modal>

      {/* Preview de imagen */}
      <Image width={0} height={0} style={{ display: 'none' }} src={previewImage}
        preview={{ visible: previewOpen, onVisibleChange: (vis) => setPreviewOpen(vis) }} />
    </div>
  );
};

export default ExecutionPage;
