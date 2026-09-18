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
  EyeOutlined, DeleteOutlined, CameraOutlined, EditOutlined, TeamOutlined, SearchOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { executionsApi, usersApi } from '../../services/api';
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
  const [secureFileUrls, setSecureFileUrls] = useState<Record<number, string>>({});
  const [selectedExecutionId, setSelectedExecutionId] = useState<number | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewImage, setPreviewImage] = useState('');
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);
  const [pdfPreviewOpen, setPdfPreviewOpen] = useState(false);
  const [pdfPreviewName, setPdfPreviewName] = useState('');

  // Estado para corrección de rechazadas
  const [correctModalOpen, setCorrectModalOpen] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<ActivityExecution | null>(null);
  const [correctForm] = Form.useForm();
  const [correctFileList, setCorrectFileList] = useState<any[]>([]);

  // Estado para filtro de TAE (approvers)
  const [taeUsers, setTaeUsers] = useState<any[]>([]);
  const [selectedTaeId, setSelectedTaeId] = useState<number | undefined>(undefined);

  const isApprover = ['Administrador', 'Coordinador', 'Supervisor'].includes(user?.role || '');

  useEffect(() => {
    if (isApprover) {
      usersApi.getAll({ role: 'TAE' }).then((users: any) => {
        setTaeUsers(Array.isArray(users) ? users : users.users || []);
      }).catch(console.error);
    }
  }, [isApprover]);

  useEffect(() => {
    loadData();
  }, [year, month, selectedTaeId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const userIdFilter = isApprover ? selectedTaeId : undefined;
      const [execsResponse, pendingResponse, statsResponse] = await Promise.all([
        executionsApi.getAll(year, month, userIdFilter),
        executionsApi.getMyToday(year, month),
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

  const getCycleNumberForDate = (target: dayjs.Dayjs) => {
    const day = target.date();
    if (day <= 10) return 1;
    if (day <= 20) return 2;
    return 3;
  };

  const getSelectedExecutionDate = () => {
    const base = dayjs(`${year}-${String(month).padStart(2, '0')}-01`);
    const day = Math.min(dayjs().date(), base.daysInMonth());
    return base.date(day);
  };

  const handleCreateExecution = async (values: any) => {
    const selectedPlanned = pendingActivities.find(
      (a) => a.planned_activity_id === values.planned_activity_id
    );
    if (selectedPlanned?.requires_evidence && fileList.length === 0) {
      message.warning('Esta actividad requiere evidencia. Adjunta al menos un archivo.');
      return;
    }

    try {
      const cycleNumber = getCycleNumberForDate(dayjs(values.execution_date));

      const result = await executionsApi.create({
        planned_activity_id: values.planned_activity_id,
        user_id: user?.id,
        organization_id: user?.organization_id,
        execution_date: values.execution_date.format('YYYY-MM-DD'),
        cycle_number: cycleNumber,
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
    if (selectedActivity.requires_evidence && quickFileList.length === 0) {
      message.warning('Esta actividad requiere evidencia. Adjunta al menos un archivo.');
      return;
    }

    try {
      const executionDate = getSelectedExecutionDate();
      const cycleNumber = getCycleNumberForDate(executionDate);

      const result = await executionsApi.create({
        planned_activity_id: selectedActivity.planned_activity_id,
        user_id: user?.id,
        organization_id: user?.organization_id,
        execution_date: executionDate.format('YYYY-MM-DD'),
        cycle_number: cycleNumber,
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
  // CORRECCIÓN DE RECHAZADAS
  // ==========================================

  const handleCorrectExecution = async (values: any) => {
    if (!selectedExecution) return;
    try {
      await executionsApi.correct(selectedExecution.id, {
        observation: values.observation,
        novelty_description: values.novelty_description,
        status: values.status,
      });
      if (correctFileList.length > 0) {
        await uploadFilesToExecution(selectedExecution.id, correctFileList);
      }
      message.success('Ejecución corregida y reenviada para aprobación');
      setCorrectModalOpen(false);
      correctForm.resetFields();
      setCorrectFileList([]);
      setSelectedExecution(null);
      loadData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al corregir');
    }
  };

  const openCorrectModal = (execution: ActivityExecution) => {
    setSelectedExecution(execution);
    correctForm.setFieldsValue({
      observation: execution.observation || '',
      novelty_description: execution.novelty_description || '',
      status: execution.status,
    });
    setCorrectModalOpen(true);
  };

  // ==========================================
  // VER EVIDENCIAS
  // ==========================================

  const openEvidenceModal = async (executionId: number) => {
    setSelectedExecutionId(executionId);
    setEvidenceModalOpen(true);
    setEvidenceLoading(true);
    setSecureFileUrls({});
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

  useEffect(() => {
    let active = true;
    const objectUrls: string[] = [];

    const loadSecureImageUrls = async () => {
      const next: Record<number, string> = {};
      for (const file of evidenceFiles) {
        if (!isImageFile(file.file_type)) continue;
        try {
          const blob = await executionsApi.getSecureFileBlob(file.file_url);
          const objectUrl = URL.createObjectURL(blob);
          objectUrls.push(objectUrl);
          next[file.id] = objectUrl;
        } catch (error) {
          console.error('Error loading secure image:', error);
        }
      }
      if (active) {
        setSecureFileUrls(next);
      } else {
        objectUrls.forEach((url) => URL.revokeObjectURL(url));
      }
    };

    if (evidenceFiles.length === 0) {
      setSecureFileUrls({});
      return () => {};
    }

    void loadSecureImageUrls();
    return () => {
      active = false;
      objectUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [evidenceFiles]);

  const handlePreviewEvidence = async (file: EvidenceFile) => {
    if (secureFileUrls[file.id]) {
      setPreviewImage(secureFileUrls[file.id]);
      setPreviewOpen(true);
      return;
    }
    try {
      const blob = await executionsApi.getSecureFileBlob(file.file_url);
      const objectUrl = URL.createObjectURL(blob);
      setPreviewImage(objectUrl);
      setPreviewOpen(true);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al abrir evidencia');
    }
  };

  const handleDownloadEvidence = async (file: EvidenceFile) => {
    try {
      const blob = await executionsApi.getSecureFileBlob(file.file_url);
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = file.file_name || 'evidencia';
      a.click();
      URL.revokeObjectURL(objectUrl);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al descargar evidencia');
    }
  };

  const handleViewEvidence = async (file: any) => {
    try {
      const blob = await executionsApi.getSecureFileBlob(file.file_url);
      const objectUrl = URL.createObjectURL(blob);
      const ext = file.file_name?.split('.').pop()?.toLowerCase() || '';
      const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'];
      if (imageExts.includes(ext)) {
        setPreviewImage(objectUrl);
        setPreviewOpen(true);
      } else {
        setPdfPreviewUrl(objectUrl);
        setPdfPreviewName(file.file_name || 'Archivo');
        setPdfPreviewOpen(true);
      }
    } catch (error) {
      message.error('Error al cargar el archivo');
    }
  };

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
      sorter: (a: ActivityExecution, b: ActivityExecution) => dayjs(a.execution_date).unix() - dayjs(b.execution_date).unix(),
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: any) => (
        <div style={{ padding: 8 }}>
          <DatePicker
            format="DD/MM/YYYY"
            value={selectedKeys[0] ? dayjs(selectedKeys[0] as string) : null}
            onChange={(date) => setSelectedKeys(date ? [date.format('YYYY-MM-DD')] : [])}
            style={{ display: 'block', marginBottom: 8 }}
          />
          <Space>
            <Button type="primary" size="small" onClick={() => confirm()}>Filtrar</Button>
            <Button size="small" onClick={() => { clearFilters?.(); confirm(); }}>Limpiar</Button>
          </Space>
        </div>
      ),
      onFilter: (value: any, record: ActivityExecution) => record.execution_date === value,
      filterIcon: (filtered: boolean) => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      render: (date: string) => dayjs(date).format('DD/MM/YY'),
    },
    {
      title: 'Actividad',
      dataIndex: 'activity_name',
      key: 'activity',
      width: 220,
      ellipsis: { showTitle: false },
      render: (text: string) => (
        <Tooltip title={text} placement="topLeft">
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block', maxWidth: 200 }}>
            {text}
          </span>
        </Tooltip>
      ),
    },
    {
      title: 'TAE',
      dataIndex: 'user_name',
      key: 'user',
      width: 150,
      ellipsis: true,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: any) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="Buscar TAE"
            value={selectedKeys[0] as string}
            onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ display: 'block', marginBottom: 8 }}
          />
          <Space>
            <Button type="primary" size="small" onClick={() => confirm()}>Buscar</Button>
            <Button size="small" onClick={() => { clearFilters?.(); confirm(); }}>Limpiar</Button>
          </Space>
        </div>
      ),
      onFilter: (value: any, record: ActivityExecution) =>
        String(record.user_name || '').toLowerCase().includes(String(value).toLowerCase()),
      filterIcon: (filtered: boolean) => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
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
      filters: [
        { text: 'Completado', value: 'Completado' },
        { text: 'Pendiente', value: 'Pendiente' },
        { text: 'Con Novedad', value: 'Con Novedad' },
        { text: 'Cancelado', value: 'Cancelado' },
      ],
      onFilter: (value: any, record: ActivityExecution) => record.status === value,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: 'Aprobación',
      dataIndex: 'approval_status',
      key: 'approval',
      width: 120,
      filters: [
        { text: 'Pendiente', value: 'Pendiente' },
        { text: 'Aprobado', value: 'Aprobado' },
        { text: 'Rechazado', value: 'Rechazado' },
      ],
      onFilter: (value: any, record: ActivityExecution) => record.approval_status === value,
      render: (status: string, record: ActivityExecution) => (
        record.approval_status === 'Rechazado' && record.rejection_reason
          ? <Tooltip title={`Motivo: ${record.rejection_reason}`}>{getApprovalTag(status)}</Tooltip>
          : getApprovalTag(status)
      ),
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
      width: 180,
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
          {record.approval_status === 'Rechazado' && Number(record.user_id) === Number(user?.id) && (
            <Tooltip title="Corregir y Reenviar">
              <Button
                type="primary"
                ghost
                size="small"
                icon={<EditOutlined />}
                onClick={() => openCorrectModal(record)}
                style={{ borderColor: '#faad14', color: '#faad14' }}
              >
                Corregir
              </Button>
            </Tooltip>
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
  const sortedPendingActivities = [...pendingActivities].sort((a, b) => {
    const byPending = b.pending - a.pending;
    if (byPending !== 0) return byPending;
    const byCompliance = a.compliance_percentage - b.compliance_percentage;
    if (byCompliance !== 0) return byCompliance;
    return (a.activity_code || '').localeCompare(b.activity_code || '');
  });

  const pendingColumns = [
    {
      title: 'Codigo',
      dataIndex: 'activity_code',
      key: 'code',
      width: 110,
      render: (code: string) => (
        <Tooltip title={code}>
          <Tag
            color="blue"
            style={{
              maxWidth: 90,
              display: 'inline-block',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              verticalAlign: 'middle',
            }}
          >
            {code}
          </Tag>
        </Tooltip>
      ),
    },
    {
      title: 'Actividad',
      dataIndex: 'activity_name',
      key: 'activity',
      width: 220,
      ellipsis: { showTitle: false },
      render: (name: string, record: PendingActivity) => (
        <Space>
          <Tooltip title={name} placement="topLeft">
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block', maxWidth: 180 }}>
              {name}
            </span>
          </Tooltip>
          {record.requires_evidence && (
            <Tooltip title="Requiere evidencia">
              <CameraOutlined style={{ color: '#faad14' }} />
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: 'Planificado',
      dataIndex: 'total_planned',
      key: 'planned',
      width: 110,
      align: 'center' as const,
    },
    {
      title: 'Ejecutado',
      dataIndex: 'total_executed',
      key: 'executed',
      width: 110,
      align: 'center' as const,
    },
    {
      title: 'Pendiente',
      dataIndex: 'pending',
      key: 'pending',
      width: 120,
      align: 'center' as const,
      sorter: (a: PendingActivity, b: PendingActivity) => a.pending - b.pending,
      defaultSortOrder: 'descend' as const,
      render: (value: number) => (
        <Tag color={value >= 5 ? 'red' : value >= 2 ? 'orange' : 'gold'}>{value}</Tag>
      ),
    },
    {
      title: 'Avance',
      key: 'compliance',
      width: 180,
      render: (_: unknown, record: PendingActivity) => (
        <Progress
          percent={record.compliance_percentage}
          size="small"
          format={() => `${record.total_executed}/${record.total_planned}`}
        />
      ),
    },
    {
      title: 'Accion',
      key: 'action',
      width: 130,
      render: (_: unknown, record: PendingActivity) => (
        <Button type="primary" size="small" icon={<CheckOutlined />} onClick={() => openQuickModal(record)}>
          Registrar
        </Button>
      ),
    },
  ];

  const uploadProps = {
    multiple: true,
    accept: 'image/*,.pdf,.doc,.docx,.xls,.xlsx,.mp4,.mov,.avi',
    beforeUpload: () => false,
    listType: 'picture' as const,
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <Title level={3} style={{ margin: 0, flexShrink: 0 }}>
            <CalendarOutlined style={{ marginRight: 8 }} />
            Registro de Ejecuciones
          </Title>
          <Text type="secondary">Gestiona y registra las actividades ejecutadas</Text>
        </div>
        <Space>
          {isApprover && taeUsers.length > 0 && (
            <Select
              value={selectedTaeId}
              onChange={(val) => setSelectedTaeId(val)}
              placeholder="Filtrar por TAE"
              allowClear
              showSearch
              optionFilterProp="label"
              style={{ width: 220 }}
              suffixIcon={<TeamOutlined />}
              options={taeUsers.map((u: any) => ({ value: u.id, label: u.full_name || u.email }))}
            />
          )}
          <Select value={month} onChange={setMonth} options={months} style={{ width: 140 }} />
          <Select
            value={year}
            onChange={setYear}
            options={[{ value: 2024, label: '2024' }, { value: 2025, label: '2025' }, { value: 2026, label: '2026' }]}
            style={{ width: 100 }}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              form.setFieldValue('execution_date', getSelectedExecutionDate());
              setModalOpen(true);
            }}
          >
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
                  <Table
                    dataSource={sortedPendingActivities}
                    columns={pendingColumns}
                    rowKey="planned_activity_id"
                    size="small"
                    scroll={{ x: 980 }}
                    pagination={{
                      defaultPageSize: 10,
                      showSizeChanger: true,
                      pageSizeOptions: ['10', '20', '50'],
                    }}
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
                <Table dataSource={executions} columns={columns} rowKey="id" loading={loading} scroll={{ x: 700 }}
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
                <Table dataSource={executions.filter(e => e.approval_status === 'Pendiente')} columns={columns} scroll={{ x: 700 }}
                  rowKey="id" loading={loading} pagination={{ defaultPageSize: 15, showSizeChanger: true, pageSizeOptions: ['15', '20', '50', '100'] }} size="small"
                  locale={{ emptyText: 'No hay ejecuciones pendientes de aprobación' }} />
              </Card>
            ),
          },
          {
            key: 'rejected',
            label: (
              <span>
                <CloseOutlined /> Rechazadas{' '}
                <Badge
                  count={executions.filter(e => e.approval_status === 'Rechazado').length}
                  style={{ marginLeft: 8, backgroundColor: '#ff4d4f' }}
                />
              </span>
            ),
            children: (
              <Card>
                <Table
                  dataSource={executions.filter(e => e.approval_status === 'Rechazado')}
                  columns={columns}
                  rowKey="id"
                  loading={loading}
                  scroll={{ x: 700 }}
                  pagination={{ defaultPageSize: 15 }}
                  size="small"
                  locale={{ emptyText: 'No hay ejecuciones rechazadas' }}
                />
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
              <Form.Item name="execution_date" label="Fecha de Ejecución" rules={[{ required: true }]} initialValue={getSelectedExecutionDate()}>
                <DatePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  disabledDate={(current) => current.year() !== year || current.month() + 1 !== month}
                />
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
          {!isApprover && (
            <Upload accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.mp4,.mov,.avi"
              showUploadList={false} beforeUpload={handleUploadToExisting}>
              <Button icon={<UploadOutlined />} size="small">Agregar Evidencia</Button>
            </Upload>
          )}
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
                        onClick={() => void handlePreviewEvidence(file)} />
                    </Tooltip>
                  ) : null,
                  !isImageFile(file.file_type) ? (
                    <Tooltip title="Ver archivo" key="view-file">
                      <Button type="link" size="small" icon={<EyeOutlined />}
                        onClick={() => void handleViewEvidence(file)} />
                    </Tooltip>
                  ) : null,
                  !isApprover ? (
                    <Tooltip title="Descargar" key="download">
                      <Button type="link" size="small" icon={<FileTextOutlined />}
                        onClick={() => void handleDownloadEvidence(file)} />
                    </Tooltip>
                  ) : null,
                  !isApprover ? (
                    <Tooltip title="Eliminar" key="delete">
                      <Button type="link" danger size="small" icon={<DeleteOutlined />}
                        onClick={() => handleDeleteFile(file.id)} />
                    </Tooltip>
                  ) : null,
                ].filter(Boolean)}
              >
                <List.Item.Meta
                  avatar={
                    isImageFile(file.file_type) ? (
                      <Image src={secureFileUrls[file.id]} width={48} height={48}
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

      {/* ===== MODAL CORRECCIÓN DE RECHAZADAS ===== */}
      <Modal
        title={
          <Space>
            <EditOutlined style={{ color: '#faad14' }} />
            <span>Corregir y Reenviar</span>
          </Space>
        }
        open={correctModalOpen}
        onCancel={() => {
          setCorrectModalOpen(false);
          setSelectedExecution(null);
          correctForm.resetFields();
          setCorrectFileList([]);
        }}
        onOk={() => correctForm.submit()}
        okText="Corregir y Reenviar"
        cancelText="Cancelar"
        width={500}
      >
        {selectedExecution && (
          <>
            <Card
              size="small"
              style={{ marginBottom: 16, backgroundColor: '#fff2e8', borderColor: '#ffbb96' }}
            >
              <Space direction="vertical" size={4}>
                <Text strong>{selectedExecution.activity_name}</Text>
                <Text type="secondary">
                  Fecha: {dayjs(selectedExecution.execution_date).format('DD/MM/YYYY')}
                </Text>
                {selectedExecution.rejection_reason && (
                  <div>
                    <Text type="danger" strong>Motivo del rechazo: </Text>
                    <Text type="danger">{selectedExecution.rejection_reason}</Text>
                  </div>
                )}
              </Space>
            </Card>
            <Form form={correctForm} layout="vertical" onFinish={handleCorrectExecution}>
              <Form.Item name="status" label="Estado" rules={[{ required: true }]}>
                <Select
                  options={[
                    { value: 'Completado', label: 'Completado' },
                    { value: 'Pendiente', label: 'Pendiente' },
                    { value: 'Con Novedad', label: 'Con Novedad' },
                  ]}
                />
              </Form.Item>
              <Form.Item name="observation" label="Observación corregida">
                <TextArea rows={3} placeholder="Describe la corrección..." />
              </Form.Item>
              <Form.Item name="novelty_description" label="Descripción de novedad">
                <TextArea rows={2} placeholder="Detalle de novedad..." />
              </Form.Item>
              <Form.Item
                label={
                  <Space>
                    <CameraOutlined />
                    <span>Adjuntar nuevas evidencias (opcional)</span>
                  </Space>
                }
              >
                <Upload
                  {...uploadProps}
                  fileList={correctFileList}
                  onChange={({ fileList: fl }) => setCorrectFileList(fl)}
                >
                  <Button icon={<UploadOutlined />}>Adjuntar Evidencia</Button>
                </Upload>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  Máx. 10MB por archivo. Formatos: imágenes, PDF, documentos Office, videos.
                </Text>
              </Form.Item>
            </Form>
          </>
        )}
      </Modal>

      {/* Preview de imagen */}
      <Image
        style={{ display: 'none' }}
        src={previewImage}
        preview={{
          visible: previewOpen,
          onVisibleChange: (v) => setPreviewOpen(v),
          toolbarRender: (_, { actions: { onZoomOut, onZoomIn, onRotateLeft, onRotateRight } }) => (
            <div style={{ display: 'flex', gap: 12, padding: '0 16px', alignItems: 'center', background: 'rgba(0,0,0,0.5)', borderRadius: 8 }}>
              <span style={{ cursor: 'pointer', color: '#fff', fontSize: 18 }} onClick={onZoomOut}>🔍−</span>
              <span style={{ cursor: 'pointer', color: '#fff', fontSize: 18 }} onClick={onZoomIn}>🔍+</span>
              <span style={{ cursor: 'pointer', color: '#fff', fontSize: 18 }} onClick={onRotateLeft}>↺</span>
              <span style={{ cursor: 'pointer', color: '#fff', fontSize: 18 }} onClick={onRotateRight}>↻</span>
            </div>
          ),
        }}
      />

      {/* Modal de previsualización de archivos (PDF, documentos) */}
      <Modal
        title={
          <Space>
            <EyeOutlined />
            <span>{pdfPreviewName}</span>
          </Space>
        }
        open={pdfPreviewOpen}
        onCancel={() => {
          setPdfPreviewOpen(false);
          if (pdfPreviewUrl) URL.revokeObjectURL(pdfPreviewUrl);
          setPdfPreviewUrl(null);
        }}
        footer={null}
        width="80vw"
        style={{ top: 20 }}
        styles={{ body: { padding: 0, height: '75vh' } }}
      >
        {pdfPreviewUrl && (
          <iframe
            src={`${pdfPreviewUrl}#toolbar=0&navpanes=0&scrollbar=1`}
            style={{ width: '100%', height: '100%', border: 'none', minHeight: '75vh' }}
            title={pdfPreviewName}
          />
        )}
      </Modal>
    </div>
  );
};

export default ExecutionPage;
