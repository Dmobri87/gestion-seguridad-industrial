// Tipos de usuario
export interface User {
  id: number;
  email: string;
  full_name: string;
  employee_code?: string;
  phone?: string;
  role: string;
  organization_id?: number;
  department_id?: number;
  work_group_id?: number;
  is_active: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginOTPResponse {
  requires_2fa: boolean;
  message: string;
  dev_otp?: string;
}

// Categorías y actividades
export interface ActivityCategory {
  id: number;
  name: string;
  code: string;
  description?: string;
  color: string;
  icon?: string;
  display_order: number;
  activities_count?: number;
}

export interface ActivityTemplate {
  id: number;
  name: string;
  code?: string;
  category_id: number;
  category_name?: string;
  category_code?: string;
  category_color?: string;
  requires_evidence: boolean;
  is_critical: boolean;
  default_frequency: number;
  display_order: number;
}

// Planificación
export interface MonthlyPlan {
  id: number;
  user_id: number;
  user_name?: string;
  user_email?: string;
  year: number;
  month: number;
  status: string;
  notes?: string;
  total_planned: number;
  total_executed: number;
  compliance_percentage: number;
  created_at: string;
}

export interface PlannedActivity {
  id: number;
  monthly_plan_id: number;
  activity_template_id: number;
  activity_name?: string;
  activity_code?: string;
  category_id?: number;
  category_name?: string;
  requires_evidence: boolean;
  cycle_1_planned: number;
  cycle_2_planned: number;
  cycle_3_planned: number;
  cycle_4_planned: number;
  cycle_1_executed: number;
  cycle_2_executed: number;
  cycle_3_executed: number;
  cycle_4_executed: number;
  total_planned: number;
  total_executed: number;
  compliance_percentage: number;
  is_critical?: boolean;
  coordinator_only?: boolean;
}

export interface PlanningCycle {
  id: number;
  cycle_number: number;
  start_date: string;
  end_date: string;
  is_current: boolean;
}

// Ejecución
export interface ActivityExecution {
  id: number;
  planned_activity_id: number;
  user_id: number;
  user_name?: string;
  activity_name?: string;
  execution_date: string;
  cycle_number: number;
  status: string;
  observation?: string;
  novelty_description?: string;
  approval_status: string;
  rejection_reason?: string;
  files_count?: number;
}

// Dashboard
export interface KPICard {
  title: string;
  value: number | string;
  unit?: string;
  icon?: string;
  color?: string;
}

export interface ComplianceByCategory {
  category_id: number;
  category_name: string;
  category_code: string;
  category_color: string;
  total_planned: number;
  total_executed: number;
  compliance_percentage: number;
}

export interface DashboardData {
  period: string;
  year: number;
  month: number;
  main_kpis: {
    accidents: KPICard;
    emergencies: KPICard;
    compliance: KPICard;
    pending_activities: KPICard;
  };
  compliance: {
    overall_compliance: number;
    by_category: ComplianceByCategory[];
    monthly_trend: {
      month: number;
      month_name: string;
      compliance_percentage: number;
    }[];
  };
  top_performers: {
    top_performers: {
      user_id: number;
      user_name: string;
      compliance_percentage: number;
      rank: number;
    }[];
  };
}

// Emergencias
export interface Emergency {
  id: number;
  emergency_code: string;
  emergency_type_id: number;
  title: string;
  description?: string;
  location?: string;
  severity: string;
  status: string;
  reported_at: string;
  response_time_minutes?: number;
}

export interface EmergencyType {
  id: number;
  name: string;
  code: string;
  color: string;
}

// Equipos
export interface Equipment {
  id: number;
  code: string;
  name: string;
  category_id: number;
  status: string;
  location?: string;
  next_maintenance_date?: string;
}

// Certificaciones
export interface UserCertification {
  id: number;
  user_id: number;
  certification_type_id: number;
  issue_date: string;
  expiry_date: string;
  status: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
