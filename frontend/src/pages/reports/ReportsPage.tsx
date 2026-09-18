import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Col, Form, InputNumber, Row, Select, Space, Spin, Table, Tag, Typography, message } from 'antd';
import { DownloadOutlined, EyeOutlined, FileExcelOutlined, FilePdfOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { reportsApi } from '../../services/api';

const { Title, Text } = Typography;

type ReportFormat = 'excel' | 'pdf';

interface ReportType {
  id: string;
  name: string;
  description: string;
  formats: ReportFormat[];
}

interface PreviewResponse {
  type: string;
  columns: { key: string; label: string }[];
  total: number;
  data: Record<string, unknown>[];
}

const monthOptions = [
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

const prettyLabel = (key: string) =>
  key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char: string) => char.toUpperCase());

const ReportsPage = () => {
  const [form] = Form.useForm();
  const [reportTypes, setReportTypes] = useState<ReportType[]>([]);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);

  useEffect(() => {
    loadReportTypes();
    form.setFieldsValue({
      report_type: 'compliance',
      format: 'excel',
      year: dayjs().year(),
      month: dayjs().month() + 1,
    });
  }, []);

  const selectedReportType = Form.useWatch('report_type', form);
  const selectedFormat = Form.useWatch('format', form);

  const availableFormats = useMemo(() => {
    const report = reportTypes.find((item) => item.id === selectedReportType);
    return report?.formats || ['excel', 'pdf'];
  }, [reportTypes, selectedReportType]);

  const columns = useMemo(() => {
    if (!preview?.columns?.length) return [];
    return preview.columns.map((column) => ({
      title: column.label || prettyLabel(column.key),
      dataIndex: column.key,
      key: column.key,
      ellipsis: true,
      render: (value: unknown) => (value === '' || value === null || value === undefined ? '-' : String(value)),
    }));
  }, [preview]);

  const loadReportTypes = async () => {
    setLoadingTypes(true);
    try {
      const response = await reportsApi.getTypes();
      setReportTypes(response);
    } catch (error) {
      console.error('Error loading report types:', error);
      message.error('No se pudieron cargar los tipos de reporte');
    } finally {
      setLoadingTypes(false);
    }
  };

  const handleReportTypeChange = (value: string) => {
    const report = reportTypes.find((item) => item.id === value);
    if (!report) return;
    if (!report.formats.includes(selectedFormat || 'excel')) {
      form.setFieldValue('format', report.formats[0]);
    }
    setPreview(null);
  };

  const getParams = (values: { year: number; month?: number; user_id?: number }) => {
    if (values.month) return values;
    const { month, ...rest } = values;
    return rest;
  };

  const handlePreview = async () => {
    try {
      const values = await form.validateFields();
      setLoadingPreview(true);
      const response = await reportsApi.getPreview(values.report_type, getParams(values));
      setPreview(response);
      message.success('Vista previa cargada');
    } catch (error: any) {
      if (!error?.errorFields) {
        console.error('Error loading preview:', error);
        message.error(error?.response?.data?.detail || 'Error al cargar la vista previa');
      }
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleDownload = async () => {
    try {
      const values = await form.validateFields();
      setDownloading(true);
      const response = await reportsApi.exportReport(values.report_type, values.format, getParams(values));
      const blob = new Blob([response.data], {
        type: values.format === 'excel'
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'application/pdf',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reporte_${values.report_type}_${values.year}${values.month ? `_${values.month}` : ''}.${values.format === 'excel' ? 'xlsx' : 'pdf'}`;
      a.click();
      URL.revokeObjectURL(url);

      message.success('Descarga iniciada');
    } catch (error: any) {
      if (!error?.errorFields) {
        console.error('Error downloading report:', error);
        message.error(error?.response?.data?.detail || 'Error al descargar el reporte');
      }
    } finally {
      setDownloading(false);
    }
  };

  if (loadingTypes) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card>
        <Title level={4} style={{ marginTop: 0 }}>
          Reportes y Exportacion
        </Title>
        <Text type="secondary">Genera reportes en Excel o PDF para cumplimiento, emergencias, equipos, certificaciones y resumen ejecutivo.</Text>

        <Form
          form={form}
          layout="vertical"
          style={{ marginTop: 16 }}
          initialValues={{ year: dayjs().year(), month: dayjs().month() + 1 }}
        >
          <Row gutter={12}>
            <Col xs={24} md={8}>
              <Form.Item name="report_type" label="Tipo de reporte" rules={[{ required: true, message: 'Selecciona un tipo de reporte' }]}>
                <Select
                  options={reportTypes.map((item) => ({ value: item.id, label: item.name }))}
                  onChange={handleReportTypeChange}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={4}>
              <Form.Item name="format" label="Formato" rules={[{ required: true, message: 'Selecciona formato' }]}>
                <Select
                  options={availableFormats.map((value) => ({
                    value,
                    label: value === 'excel' ? 'Excel' : 'PDF',
                  }))}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={4}>
              <Form.Item name="year" label="Ano" rules={[{ required: true, message: 'Ingresa ano' }]}>
                <InputNumber min={2020} max={2100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={4}>
              <Form.Item name="month" label="Mes">
                <Select allowClear options={monthOptions} placeholder="Anual" />
              </Form.Item>
            </Col>
            <Col xs={24} md={4}>
              <Form.Item name="user_id" label="Usuario (opcional)">
                <InputNumber min={1} style={{ width: '100%' }} placeholder="ID usuario" />
              </Form.Item>
            </Col>
          </Row>
        </Form>

        <Space>
          <Button type="default" icon={<EyeOutlined />} onClick={handlePreview} loading={loadingPreview}>
            Vista previa
          </Button>
          <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownload} loading={downloading}>
            Descargar
          </Button>
          <Tag color={selectedFormat === 'pdf' ? 'red' : 'green'} icon={selectedFormat === 'pdf' ? <FilePdfOutlined /> : <FileExcelOutlined />}>
            {selectedFormat === 'pdf' ? 'PDF' : 'Excel'}
          </Tag>
        </Space>
      </Card>

      <Card title="Vista previa">
        {!preview && (
          <Alert
            type="info"
            showIcon
            message="Sin vista previa"
            description="Selecciona los filtros y haz clic en Vista previa para cargar los datos."
          />
        )}

        {preview && (
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Text>
              <strong>Registros:</strong> {preview.total}
            </Text>
            <Table
              columns={columns}
              dataSource={preview.data.slice(0, 100).map((row, index) => ({ ...row, key: index }))}
              scroll={{ x: true }}
              pagination={{ pageSize: 10, showSizeChanger: false }}
              size="small"
              locale={{ emptyText: 'No hay datos para este filtro.' }}
            />
          </Space>
        )}
      </Card>
    </Space>
  );
};

export default ReportsPage;
