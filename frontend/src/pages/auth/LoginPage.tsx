import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, message, Typography, Alert, Space } from 'antd';
import {
  UserOutlined,
  LockOutlined,
  SafetyOutlined,
  MailOutlined,
  ArrowLeftOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { authApi } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

const { Title, Text, Paragraph } = Typography;

interface LoginForm {
  email: string;
  password: string;
}

// Utility to mask an email: d***@outlook.es
const maskEmail = (email: string): string => {
  const [local, domain] = email.split('@');
  if (!domain) return email;
  const masked = local.length > 1
    ? local[0] + '***'
    : local + '***';
  return `${masked}@${domain}`;
};

// OTP expiration in seconds
const OTP_EXPIRATION_SECONDS = 5 * 60;

const LoginPage = () => {
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'credentials' | 'otp'>('credentials');
  const [otpValues, setOtpValues] = useState<string[]>(['', '', '', '', '', '', '', '']);
  const [countdown, setCountdown] = useState(OTP_EXPIRATION_SECONDS);
  const [resendLoading, setResendLoading] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);
  const setPending2FA = useAuthStore((state) => state.setPending2FA);
  const devOtp = useAuthStore((state) => state.devOtp);
  const clear2FA = useAuthStore((state) => state.clear2FA);

  const otpInputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Countdown timer for OTP expiration
  useEffect(() => {
    if (step === 'otp') {
      setCountdown(OTP_EXPIRATION_SECONDS);
      countdownRef.current = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            if (countdownRef.current) clearInterval(countdownRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, [step]);

  // Format countdown as MM:SS
  const formatCountdown = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Focus first OTP input when entering OTP step
  useEffect(() => {
    if (step === 'otp') {
      setTimeout(() => {
        otpInputRefs.current[0]?.focus();
      }, 100);
    }
  }, [step]);

  // Step 1: Submit credentials
  const onFinish = async (values: LoginForm) => {
    setLoading(true);
    setLoginEmail(values.email);
    setLoginPassword(values.password);
    try {
      const response = await authApi.login(values.email, values.password);

      if (response.requires_2fa) {
        setPending2FA(values.email, response.dev_otp || null);
        setStep('otp');
        setOtpValues(['', '', '', '', '', '', '', '']);
        message.info('CÃ³digo de verificaciÃ³n enviado a su email');
      } else if (response.access_token) {
        // Fallback: direct token (should not happen with mandatory 2FA)
        setAuth(response.user, response.access_token);
        message.success(`Bienvenido, ${response.user.full_name}`);
        navigate('/dashboard');
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Error al iniciar sesiÃ³n';
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP (8 digits)
  const handleVerifyOtp = useCallback(async (otpCode: string) => {
    if (otpCode.length !== 8) return;

    setLoading(true);
    try {
      const response = await authApi.verifyOtp(loginEmail, otpCode);
      setAuth(response.user, response.access_token);
      clear2FA();
      message.success(`Bienvenido, ${response.user.full_name}`);
      navigate('/dashboard');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Error al verificar el cÃ³digo';
      message.error(errorMessage);
      // Clear OTP inputs on error
      setOtpValues(['', '', '', '', '', '', '', '']);
      setTimeout(() => {
        otpInputRefs.current[0]?.focus();
      }, 100);
    } finally {
      setLoading(false);
    }
  }, [loginEmail, setAuth, clear2FA, navigate]);

  // Handle OTP digit input
  const handleOtpChange = (index: number, value: string) => {
    // Only allow digits
    const digit = value.replace(/\D/g, '').slice(-1);
    const newValues = [...otpValues];
    newValues[index] = digit;
    setOtpValues(newValues);

    if (digit && index < 7) {
      // Move to next input
      otpInputRefs.current[index + 1]?.focus();
    }

    // Auto-submit when all 8 digits are entered
    const fullCode = newValues.join('');
    if (fullCode.length === 8 && newValues.every((v) => v !== '')) {
      handleVerifyOtp(fullCode);
    }
  };

  // Handle paste in OTP inputs
  const handleOtpPaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 8);
    if (pastedData.length > 0) {
      const newValues = [...otpValues];
      for (let i = 0; i < 8; i++) {
        newValues[i] = pastedData[i] || '';
      }
      setOtpValues(newValues);

      // Focus last filled or next empty
      const focusIndex = Math.min(pastedData.length, 7);
      otpInputRefs.current[focusIndex]?.focus();

      // Auto-submit if all 8 digits pasted
      if (pastedData.length === 8) {
        handleVerifyOtp(pastedData);
      }
    }
  };

  // Handle backspace in OTP inputs
  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otpValues[index] && index > 0) {
      otpInputRefs.current[index - 1]?.focus();
      const newValues = [...otpValues];
      newValues[index - 1] = '';
      setOtpValues(newValues);
    }
  };

  // Resend OTP
  const handleResendOtp = async () => {
    if (!loginEmail || !loginPassword) {
      message.error('Error interno. Vuelva a iniciar sesiÃ³n.');
      handleBackToLogin();
      return;
    }

    setResendLoading(true);
    try {
      const response = await authApi.login(loginEmail, loginPassword);
      if (response.requires_2fa) {
        setPending2FA(loginEmail, response.dev_otp || null);
        setOtpValues(['', '', '', '', '', '', '', '']);
        setCountdown(OTP_EXPIRATION_SECONDS);
        // Restart timer
        if (countdownRef.current) clearInterval(countdownRef.current);
        countdownRef.current = setInterval(() => {
          setCountdown((prev) => {
            if (prev <= 1) {
              if (countdownRef.current) clearInterval(countdownRef.current);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
        message.success('Nuevo cÃ³digo de verificaciÃ³n enviado');
        setTimeout(() => {
          otpInputRefs.current[0]?.focus();
        }, 100);
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Error al reenviar el cÃ³digo';
      message.error(errorMessage);
    } finally {
      setResendLoading(false);
    }
  };

  // Go back to credentials step
  const handleBackToLogin = () => {
    clear2FA();
    setStep('credentials');
    setOtpValues(['', '', '', '', '', '', '', '']);
    setLoginPassword('');
    if (countdownRef.current) clearInterval(countdownRef.current);
  };

  // Manual submit OTP button
  const handleManualOtpSubmit = () => {
    const code = otpValues.join('');
    if (code.length === 8) {
      handleVerifyOtp(code);
    } else {
      message.warning('Ingrese los 8 digitos del codigo de verificacion');
    }
  };

  return (
    <div className="login-container">
      <Card className="login-card" style={{ width: step === 'otp' ? 500 : 400 }}>
        {/* â”€â”€ Step 1: Email + Password â”€â”€ */}
        {step === 'credentials' && (
          <>
            <div className="login-title">
              <SafetyOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
              <Title level={3}>Gesti&oacute;n GAE</Title>
              <Text type="secondary">Sistema de Gesti&oacute;n Empresarial</Text>
            </div>

            <Form
              name="login"
              onFinish={onFinish}
              autoComplete="off"
              layout="vertical"
              size="large"
            >
              <Form.Item
                name="email"
                rules={[
                  { required: true, message: 'Ingresa tu email' },
                  { type: 'email', message: 'Email no v\u00e1lido' },
                ]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="Email"
                />
              </Form.Item>

              <Form.Item
                name="password"
                rules={[{ required: true, message: 'Ingresa tu Contraseña' }]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="Contraseña"
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  block
                >
                  Iniciar Sesi&oacute;n
                </Button>
              </Form.Item>
            </Form>

            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                Gesti&oacute;n GAE v2.0
              </Text>
            </div>
          </>
        )}

        {/* â”€â”€ Step 2: OTP Verification â”€â”€ */}
        {step === 'otp' && (
          <>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <div
                style={{
                  width: 72,
                  height: 72,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 20px',
                  boxShadow: '0 4px 14px rgba(24, 144, 255, 0.3)',
                }}
              >
                <MailOutlined style={{ fontSize: 32, color: '#fff' }} />
              </div>

              <Title level={4} style={{ marginBottom: 8 }}>
                Verificaci&oacute;n de identidad
              </Title>

              <Paragraph
                type="secondary"
                style={{ marginBottom: 4, fontSize: 14 }}
              >
                Ingrese el c&oacute;digo de verificaci&oacute;n enviado a su correo electr&oacute;nico
              </Paragraph>

              <Text
                strong
                style={{ fontSize: 14, color: '#1890ff' }}
              >
                {maskEmail(loginEmail)}
              </Text>
            </div>

            {/* Dev mode banner */}
            {devOtp && (
              <Alert
                message={`Modo desarrollo - C\u00f3digo OTP: ${devOtp}`}
                type="warning"
                showIcon
                style={{ marginBottom: 20, textAlign: 'center' }}
                banner
              />
            )}

            {/* OTP Input Boxes */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                gap: 10,
                marginBottom: 20,
              }}
              onPaste={handleOtpPaste}
            >
              {otpValues.map((value, index) => (
                <input
                  key={index}
                  ref={(el) => { otpInputRefs.current[index] = el; }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={value}
                  onChange={(e) => handleOtpChange(index, e.target.value)}
                  onKeyDown={(e) => handleOtpKeyDown(index, e)}
                  disabled={loading}
                  style={{
                    width: 42,
                    height: 52,
                    textAlign: 'center',
                    fontSize: 22,
                    fontWeight: 700,
                    fontFamily: "'Courier New', monospace",
                    border: value
                      ? '2px solid #1890ff'
                      : '2px solid #d9d9d9',
                    borderRadius: 10,
                    outline: 'none',
                    transition: 'all 0.2s ease',
                    background: value ? '#f0f5ff' : '#fff',
                    color: '#1a365d',
                    boxShadow: value
                      ? '0 0 0 2px rgba(24, 144, 255, 0.15)'
                      : 'none',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#1890ff';
                    e.target.style.boxShadow = '0 0 0 3px rgba(24, 144, 255, 0.2)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = value ? '#1890ff' : '#d9d9d9';
                    e.target.style.boxShadow = value
                      ? '0 0 0 2px rgba(24, 144, 255, 0.15)'
                      : 'none';
                  }}
                />
              ))}
            </div>

            {/* Countdown Timer */}
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              {countdown > 0 ? (
                <Text
                  type="secondary"
                  style={{
                    fontSize: 14,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  El c&oacute;digo expira en{' '}
                  <Text
                    strong
                    style={{
                      color: countdown <= 60 ? '#ff4d4f' : '#1890ff',
                      fontSize: 16,
                      fontFamily: "'Courier New', monospace",
                    }}
                  >
                    {formatCountdown(countdown)}
                  </Text>
                </Text>
              ) : (
                <Text type="danger" style={{ fontSize: 14 }}>
                  El c&oacute;digo ha expirado. Solicite uno nuevo.
                </Text>
              )}
            </div>

            {/* Verify Button */}
            <Button
              type="primary"
              size="large"
              block
              loading={loading}
              onClick={handleManualOtpSubmit}
              disabled={otpValues.join('').length !== 8 || countdown === 0}
              style={{ marginBottom: 16, height: 44 }}
            >
              Verificar
            </Button>

            {/* Action links */}
            <Space
              direction="vertical"
              size={8}
              style={{ width: '100%', textAlign: 'center' }}
            >
              <Button
                type="link"
                icon={<ReloadOutlined />}
                onClick={handleResendOtp}
                loading={resendLoading}
                disabled={loading}
                style={{ padding: 0 }}
              >
                Reenviar c&oacute;digo
              </Button>

              <Button
                type="link"
                icon={<ArrowLeftOutlined />}
                onClick={handleBackToLogin}
                disabled={loading}
                style={{ padding: 0, color: '#8c8c8c' }}
              >
                Volver al inicio de sesi&oacute;n
              </Button>
            </Space>
          </>
        )}
      </Card>
    </div>
  );
};

export default LoginPage;
