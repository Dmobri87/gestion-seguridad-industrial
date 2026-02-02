"""
Script para poblar la base de datos con datos de prueba.
Ejecutar: python seed_data.py
"""
from datetime import datetime, date, timedelta
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import (
    Organization, Department, User,
    ActivityCategory, ActivityTemplate,
    MonthlyPlan, PlanningCycle, PlannedActivity,
    ActivityExecution,
    EmergencyType, Emergency,
    EquipmentCategory, Equipment,
    CertificationType, UserCertification
)

def seed_database():
    db = SessionLocal()

    try:
        org = db.query(Organization).first()
        dept = db.query(Department).first()
        admin = db.query(User).first()

        # Verificar si ya hay datos
        if db.query(ActivityCategory).count() > 0:
            print("Ya existen datos de prueba. Abortando.")
            return

        print("=== CREANDO DATOS DE PRUEBA ===")
        print("")

        # ========== DEPARTAMENTOS ADICIONALES ==========
        dept_ops = Department(name="Operaciones", code="OPS", organization_id=org.id, is_active=True)
        dept_seg = Department(name="Seguridad", code="SEG", organization_id=org.id, is_active=True)
        dept_emer = Department(name="Emergencias", code="EMER", organization_id=org.id, is_active=True)
        db.add_all([dept_ops, dept_seg, dept_emer])
        db.flush()
        print("[OK] Departamentos creados")

        # ========== USUARIOS TAE ==========
        users = [
            User(email="juan.perez@empresa.com", hashed_password=get_password_hash("tae123"),
                 full_name="Juan Perez", employee_code="TAE001", role="TAE",
                 organization_id=org.id, department_id=dept_emer.id, is_active=True, is_verified=True),
            User(email="maria.garcia@empresa.com", hashed_password=get_password_hash("tae123"),
                 full_name="Maria Garcia", employee_code="TAE002", role="TAE",
                 organization_id=org.id, department_id=dept_emer.id, is_active=True, is_verified=True),
            User(email="carlos.lopez@empresa.com", hashed_password=get_password_hash("tae123"),
                 full_name="Carlos Lopez", employee_code="TAE003", role="TAE",
                 organization_id=org.id, department_id=dept_emer.id, is_active=True, is_verified=True),
            User(email="supervisor@empresa.com", hashed_password=get_password_hash("super123"),
                 full_name="Ana Martinez", employee_code="SUP001", role="Supervisor",
                 organization_id=org.id, department_id=dept_seg.id, is_active=True, is_verified=True),
        ]
        db.add_all(users)
        db.flush()
        print("[OK] 4 usuarios creados (3 TAE + 1 Supervisor)")

        # ========== CATEGORIAS DE ACTIVIDADES (Basadas en imagen real) ==========
        categories = [
            ActivityCategory(name="Inspeccion GRID Operacional", code="GRID",
                           description="Inspecciones del Grid Operacional",
                           color="#1890ff", display_order=1, organization_id=org.id),
            ActivityCategory(name="Actividades de Soporte", code="SOPORTE",
                           description="Actividades de soporte y seguimiento",
                           color="#52c41a", display_order=2, organization_id=org.id),
            ActivityCategory(name="Entrenamiento", code="ENTRENA",
                           description="Actividades de entrenamiento y capacitacion",
                           color="#faad14", display_order=3, organization_id=org.id),
        ]
        db.add_all(categories)
        db.flush()
        print("[OK] 3 categorias de actividades creadas")

        # ========== PLANTILLAS DE ACTIVIDADES (Basadas en imagen real) ==========
        templates = []

        # CATEGORIA: INSPECCION GRID OPERACIONAL
        grid_activities = [
            ("Maquina", "GRID-MAQ", True),
            ("Ambulancia", "GRID-AMB", True),
            ("CAE", "GRID-CAE", True),
            ("Inspeccion de Vias y ubicacion de Equipos de Cargue", "GRID-VIAS", True),
            ("Recordacion de riesgo en la conduccion", "GRID-RCON", False),
            ("Recordacion de riesgo en la atencion de la emergencia", "GRID-REMER", False),
            ("Esquema de emergencia", "GRID-ESQ", True),
            ("Inspecciones SIO", "GRID-SIO", True),
            ("Observaciones de Conduccion de Equipos Liviano/Mediano", "GRID-OBS", True),
            ("No. Observaciones de Tareas Criticas (Bimensual)", "GRID-TC", True),
            ("Reporte CAS (1 X Trimestre) y verificar cierre", "GRID-CAS", True),
        ]
        for name, code, requires_evidence in grid_activities:
            templates.append(ActivityTemplate(
                name=name, code=code, category_id=categories[0].id,
                description=f"Actividad: {name}", default_frequency=1,
                requires_evidence=requires_evidence, organization_id=org.id
            ))

        # CATEGORIA: ACTIVIDADES DE SOPORTE
        soporte_activities = [
            ("Aseo de Ambulancias por Aseocolba", "SOP-ASEO", False),
            ("Asistencia a reunion diaria (G-COM)", "SOP-GCOM", False),
            ("Cumplir estandar de entregas de equipo a taller", "SOP-TALL", True),
            ("Auditoria de SSI en equipo Minero", "SOP-SSI", True),
            ("Enviar informe de disponibilidad diaria de las Unidades de Emergencia y los Kilometrajes / Horometros fin de semana", "SOP-DISP", True),
            ("Envio de Informe de faltantes de la maquina (Inventario)", "SOP-INV", True),
            ("Inventario de dotacion de Ambulancias", "SOP-DOTAMB", True),
            ("Actualizar tablero de indicador de desempeno individual y asegurar el soporte documental de sus actividades", "SOP-IND", True),
            ("Mantenimiento de unidades de emergencia", "SOP-MANT", True),
            ("Seguimiento Proceso", "SOP-PROC", False),
            ("Seguimiento Soporte de Proceso", "SOP-SPROC", False),
            ("Citacion de Alcohol y Drogas", "SOP-CITAD", True),
            ("Muestreo de Alcohol y Drogas", "SOP-MUEAD", True),
            ("Enviar informe de resultados de Alcohol y Drogas", "SOP-INFAD", True),
            ("Recepcion de Reportes de Tareas Criticas", "SOP-REPTC", True),
        ]
        for name, code, requires_evidence in soporte_activities:
            templates.append(ActivityTemplate(
                name=name, code=code, category_id=categories[1].id,
                description=f"Actividad: {name}", default_frequency=1,
                requires_evidence=requires_evidence, organization_id=org.id
            ))

        # CATEGORIA: ENTRENAMIENTO
        entrena_activities = [
            ("Entrenamiento Mensual", "ENT-MENS", True),
            ("Colocacion de EPP contra Incendio (Tiempo)", "ENT-EPP", True),
            ("Postura de Arnes (Tiempo)", "ENT-ARNES", True),
            ("Estudio de Normas NFPA", "ENT-NFPA", False),
        ]
        for name, code, requires_evidence in entrena_activities:
            templates.append(ActivityTemplate(
                name=name, code=code, category_id=categories[2].id,
                description=f"Actividad: {name}", default_frequency=1,
                requires_evidence=requires_evidence, organization_id=org.id
            ))

        db.add_all(templates)
        db.flush()
        print(f"[OK] {len(templates)} plantillas de actividades creadas")

        # ========== TIPOS DE EMERGENCIA ==========
        emergency_types = [
            EmergencyType(name="Incendio Estructural", code="INC-EST", default_severity="Critica", target_response_time=5, color="#ff4d4f"),
            EmergencyType(name="Incendio Vehicular", code="INC-VEH", default_severity="Alta", target_response_time=5, color="#ff4d4f"),
            EmergencyType(name="Accidente de Transito", code="ACC-TRAN", default_severity="Alta", target_response_time=8, color="#faad14"),
            EmergencyType(name="Accidente Laboral", code="ACC-LAB", default_severity="Media", target_response_time=10, color="#faad14"),
            EmergencyType(name="Emergencia Medica", code="EMER-MED", default_severity="Alta", target_response_time=8, color="#1890ff"),
            EmergencyType(name="Derrame de Sustancias", code="DER-SUST", default_severity="Alta", target_response_time=10, color="#722ed1"),
            EmergencyType(name="Rescate en Altura", code="RES-ALT", default_severity="Critica", target_response_time=10, color="#ff4d4f"),
            EmergencyType(name="Rescate en Espacio Confinado", code="RES-EC", default_severity="Critica", target_response_time=10, color="#ff4d4f"),
        ]
        db.add_all(emergency_types)
        db.flush()
        print("[OK] 8 tipos de emergencia creados")

        # ========== CATEGORIAS DE EQUIPOS ==========
        equip_categories = [
            EquipmentCategory(name="Ambulancias", code="AMB", description="Unidades de emergencia medica"),
            EquipmentCategory(name="Vehiculos de Rescate", code="RESC", description="Vehiculos especializados de rescate"),
            EquipmentCategory(name="Extintores", code="EXT", description="Extintores portatiles y rodantes"),
            EquipmentCategory(name="SCBA", code="SCBA", description="Equipos de respiracion autonoma"),
            EquipmentCategory(name="Equipos de Rescate", code="EQ-RESC", description="Herramientas y equipos de rescate"),
            EquipmentCategory(name="Comunicaciones", code="COM", description="Radios y equipos de comunicacion"),
        ]
        db.add_all(equip_categories)
        db.flush()
        print("[OK] 6 categorias de equipos creadas")

        # ========== EQUIPOS ==========
        equipments = [
            Equipment(name="Ambulancia TAE-01", code="AMB-001", serial_number="VIN001", category_id=equip_categories[0].id,
                     location="Base Principal", status="Operativo", last_maintenance_date=date.today() - timedelta(days=15),
                     next_maintenance_date=date.today() + timedelta(days=75), organization_id=org.id),
            Equipment(name="Ambulancia TAE-02", code="AMB-002", serial_number="VIN002", category_id=equip_categories[0].id,
                     location="Base Norte", status="Operativo", last_maintenance_date=date.today() - timedelta(days=30),
                     next_maintenance_date=date.today() + timedelta(days=60), organization_id=org.id),
            Equipment(name="Camioneta Rescate", code="RESC-001", serial_number="VIN003", category_id=equip_categories[1].id,
                     location="Base Principal", status="Operativo", last_maintenance_date=date.today(),
                     next_maintenance_date=date.today() + timedelta(days=90), organization_id=org.id),
            Equipment(name="SCBA Drager PSS-7000", code="SCBA-001", serial_number="DRG001", category_id=equip_categories[3].id,
                     location="Ambulancia TAE-01", status="Operativo", last_maintenance_date=date.today(),
                     next_maintenance_date=date.today() + timedelta(days=365), organization_id=org.id),
            Equipment(name="SCBA Drager PSS-7000", code="SCBA-002", serial_number="DRG002", category_id=equip_categories[3].id,
                     location="Ambulancia TAE-02", status="Operativo", last_maintenance_date=date.today(),
                     next_maintenance_date=date.today() + timedelta(days=365), organization_id=org.id),
            Equipment(name="Extintor PQS 20lb", code="EXT-001", serial_number="EXT001", category_id=equip_categories[2].id,
                     location="Ambulancia TAE-01", status="Operativo", last_maintenance_date=date.today(),
                     next_maintenance_date=date.today() + timedelta(days=180), organization_id=org.id),
            Equipment(name="Radio Motorola DGP8550", code="RAD-001", serial_number="MOT001", category_id=equip_categories[5].id,
                     location="Ambulancia TAE-01", status="Operativo", last_maintenance_date=date.today(),
                     next_maintenance_date=date.today() + timedelta(days=365), organization_id=org.id),
        ]
        db.add_all(equipments)
        db.flush()
        print("[OK] 7 equipos creados")

        # ========== TIPOS DE CERTIFICACION ==========
        cert_types = [
            CertificationType(name="Licencia de Conducir C2", code="LIC-C2", applies_to="personal", default_validity_days=1825, is_mandatory=True),
            CertificationType(name="Certificado Trabajo en Altura", code="ALTURA", applies_to="personal", default_validity_days=365, is_mandatory=True),
            CertificationType(name="Certificado Espacios Confinados", code="ESP-CONF", applies_to="personal", default_validity_days=365, is_mandatory=True),
            CertificationType(name="Certificado Primeros Auxilios Avanzados", code="PAA", applies_to="personal", default_validity_days=730, is_mandatory=True),
            CertificationType(name="Certificado Manejo Defensivo", code="MAN-DEF", applies_to="personal", default_validity_days=365, is_mandatory=True),
            CertificationType(name="Certificado Bombero Industrial", code="BOMB-IND", applies_to="personal", default_validity_days=365, is_mandatory=True),
            CertificationType(name="SOAT", code="SOAT", applies_to="vehicle", default_validity_days=365, is_mandatory=True),
            CertificationType(name="Revision Tecnico Mecanica", code="RTM", applies_to="vehicle", default_validity_days=365, is_mandatory=True),
        ]
        db.add_all(cert_types)
        db.flush()
        print("[OK] 8 tipos de certificacion creados")

        # ========== CERTIFICACIONES DE USUARIOS ==========
        certs = [
            # Juan Perez - Todas sus certificaciones
            UserCertification(user_id=users[0].id, certification_type_id=cert_types[0].id,
                             issue_date=date.today() - timedelta(days=365), expiry_date=date.today() + timedelta(days=1460),
                             issuing_entity="Ministerio de Transporte", certificate_number="LIC-JP-001", organization_id=org.id),
            UserCertification(user_id=users[0].id, certification_type_id=cert_types[1].id,
                             issue_date=date.today() - timedelta(days=180), expiry_date=date.today() + timedelta(days=185),
                             issuing_entity="SENA", certificate_number="ALT-JP-001", organization_id=org.id),
            UserCertification(user_id=users[0].id, certification_type_id=cert_types[3].id,
                             issue_date=date.today() - timedelta(days=100), expiry_date=date.today() + timedelta(days=630),
                             issuing_entity="Cruz Roja", certificate_number="PAA-JP-001", organization_id=org.id),
            UserCertification(user_id=users[0].id, certification_type_id=cert_types[5].id,
                             issue_date=date.today() - timedelta(days=200), expiry_date=date.today() + timedelta(days=165),
                             issuing_entity="Bomberos Colombia", certificate_number="BOMB-JP-001", organization_id=org.id),

            # Maria Garcia
            UserCertification(user_id=users[1].id, certification_type_id=cert_types[0].id,
                             issue_date=date.today() - timedelta(days=500), expiry_date=date.today() + timedelta(days=1325),
                             issuing_entity="Ministerio de Transporte", certificate_number="LIC-MG-001", organization_id=org.id),
            UserCertification(user_id=users[1].id, certification_type_id=cert_types[4].id,
                             issue_date=date.today() - timedelta(days=300), expiry_date=date.today() + timedelta(days=65),
                             issuing_entity="Consejo Colombiano de Seguridad", certificate_number="MD-MG-001", organization_id=org.id),

            # Carlos Lopez - Certificacion proxima a vencer (10 dias)
            UserCertification(user_id=users[2].id, certification_type_id=cert_types[1].id,
                             issue_date=date.today() - timedelta(days=355), expiry_date=date.today() + timedelta(days=10),
                             issuing_entity="SENA", certificate_number="ALT-CL-001", organization_id=org.id),
            UserCertification(user_id=users[2].id, certification_type_id=cert_types[2].id,
                             issue_date=date.today() - timedelta(days=340), expiry_date=date.today() + timedelta(days=25),
                             issuing_entity="SENA", certificate_number="EC-CL-001", organization_id=org.id),
        ]
        db.add_all(certs)
        db.flush()
        print("[OK] 8 certificaciones de usuarios creadas")

        # ========== PLAN MENSUAL ==========
        plan = MonthlyPlan(
            user_id=users[0].id,
            year=2026,
            month=1,
            status="Aprobado",
            created_by=admin.id,
            organization_id=org.id
        )
        db.add(plan)
        db.flush()
        print("[OK] Plan mensual de Enero 2026 creado")

        # ========== CICLOS DE PLANIFICACION ==========
        cycles = [
            PlanningCycle(monthly_plan_id=plan.id, cycle_number=1, start_date=date(2026,1,1), end_date=date(2026,1,7)),
            PlanningCycle(monthly_plan_id=plan.id, cycle_number=2, start_date=date(2026,1,8), end_date=date(2026,1,14)),
            PlanningCycle(monthly_plan_id=plan.id, cycle_number=3, start_date=date(2026,1,15), end_date=date(2026,1,21)),
            PlanningCycle(monthly_plan_id=plan.id, cycle_number=4, start_date=date(2026,1,22), end_date=date(2026,1,31)),
        ]
        db.add_all(cycles)
        db.flush()
        print("[OK] 4 ciclos de planificacion creados")

        # ========== ACTIVIDADES PLANEADAS ==========
        # Obtener templates por codigo
        tpl_amb = db.query(ActivityTemplate).filter(ActivityTemplate.code == "GRID-AMB").first()
        tpl_maq = db.query(ActivityTemplate).filter(ActivityTemplate.code == "GRID-MAQ").first()
        tpl_gcom = db.query(ActivityTemplate).filter(ActivityTemplate.code == "SOP-GCOM").first()
        tpl_sio = db.query(ActivityTemplate).filter(ActivityTemplate.code == "GRID-SIO").first()
        tpl_ent = db.query(ActivityTemplate).filter(ActivityTemplate.code == "ENT-MENS").first()

        planned = [
            PlannedActivity(monthly_plan_id=plan.id, activity_template_id=tpl_amb.id,
                           cycle_1_planned=7, cycle_2_planned=7, cycle_3_planned=7, cycle_4_planned=7,
                           total_planned=28, cycle_1_executed=7, total_executed=7),
            PlannedActivity(monthly_plan_id=plan.id, activity_template_id=tpl_maq.id,
                           cycle_1_planned=7, cycle_2_planned=7, cycle_3_planned=7, cycle_4_planned=7,
                           total_planned=28, cycle_1_executed=7, total_executed=7),
            PlannedActivity(monthly_plan_id=plan.id, activity_template_id=tpl_gcom.id,
                           cycle_1_planned=5, cycle_2_planned=5, cycle_3_planned=5, cycle_4_planned=5,
                           total_planned=20, cycle_1_executed=5, cycle_2_executed=5, total_executed=10),
            PlannedActivity(monthly_plan_id=plan.id, activity_template_id=tpl_sio.id,
                           cycle_1_planned=2, cycle_2_planned=2, cycle_3_planned=2, cycle_4_planned=2,
                           total_planned=8, total_executed=0),
            PlannedActivity(monthly_plan_id=plan.id, activity_template_id=tpl_ent.id,
                           cycle_1_planned=0, cycle_2_planned=0, cycle_3_planned=0, cycle_4_planned=1,
                           total_planned=1, total_executed=0),
        ]
        db.add_all(planned)
        db.flush()
        print("[OK] 5 actividades planeadas creadas")

        # ========== EJECUCIONES ==========
        executions = [
            ActivityExecution(planned_activity_id=planned[0].id, user_id=users[0].id,
                             execution_date=date(2026,1,6), cycle_number=1, status="Completado",
                             observation="Ambulancia inspeccionada, todo operativo", quantity=7, approval_status="Aprobado",
                             approved_by=admin.id, organization_id=org.id),
            ActivityExecution(planned_activity_id=planned[1].id, user_id=users[0].id,
                             execution_date=date(2026,1,6), cycle_number=1, status="Completado",
                             observation="Maquina en buen estado", quantity=7, approval_status="Aprobado",
                             approved_by=admin.id, organization_id=org.id),
            ActivityExecution(planned_activity_id=planned[2].id, user_id=users[0].id,
                             execution_date=date(2026,1,10), cycle_number=2, status="Completado",
                             observation="Asistencia completa a G-COM", quantity=5, approval_status="Pendiente",
                             organization_id=org.id),
        ]
        db.add_all(executions)
        db.flush()
        print("[OK] 3 ejecuciones creadas (2 aprobadas, 1 pendiente)")

        # ========== EMERGENCIAS ==========
        emergencies = [
            Emergency(emergency_type_id=emergency_types[3].id, reported_by=users[0].id,
                     emergency_code="EMG-2026-0001",
                     title="Lesion en mano por herramienta",
                     description="Trabajador con corte en mano derecha durante mantenimiento",
                     location="Taller de Mantenimiento - Nivel 2", severity="Media", status="Cerrada",
                     reported_at=datetime(2026,1,5,9,30), arrival_at=datetime(2026,1,5,9,38),
                     closed_at=datetime(2026,1,5,10,15), actions_taken="Primeros auxilios, curacion y vendaje",
                     result="Trabajador remitido a ARL para seguimiento",
                     organization_id=org.id, response_time_minutes=8),
            Emergency(emergency_type_id=emergency_types[2].id, reported_by=users[1].id,
                     emergency_code="EMG-2026-0002",
                     title="Colision menor en via interna",
                     description="Colision entre camioneta y poste de senalizacion",
                     location="Via principal Km 3.5", severity="Baja", status="Cerrada",
                     reported_at=datetime(2026,1,8,14,0), arrival_at=datetime(2026,1,8,14,12),
                     closed_at=datetime(2026,1,8,15,30), actions_taken="Evaluacion de danos, reporte fotografico",
                     result="Sin lesionados, danos menores al vehiculo",
                     organization_id=org.id, response_time_minutes=12),
            Emergency(emergency_type_id=emergency_types[4].id, reported_by=users[0].id,
                     emergency_code="EMG-2026-0003",
                     title="Dolor toracico en trabajador",
                     description="Operador reporta dolor en pecho durante turno",
                     location="Sala de Control - Edificio Administrativo", severity="Alta", status="Cerrada",
                     reported_at=datetime(2026,1,15,11,20), arrival_at=datetime(2026,1,15,11,26),
                     closed_at=datetime(2026,1,15,12,45), actions_taken="Monitoreo de signos vitales, oxigeno, traslado a clinica",
                     result="Paciente estable, trasladado a Clinica del Norte para evaluacion cardiologica",
                     organization_id=org.id, response_time_minutes=6),
        ]
        db.add_all(emergencies)
        db.commit()
        print("[OK] 3 emergencias historicas creadas")

        print("")
        print("========================================")
        print("    DATOS DE PRUEBA CREADOS")
        print("========================================")
        print("")
        print("USUARIOS:")
        print("  - admin@empresa.com / admin123 (Administrador)")
        print("  - supervisor@empresa.com / super123 (Supervisor)")
        print("  - juan.perez@empresa.com / tae123 (TAE)")
        print("  - maria.garcia@empresa.com / tae123 (TAE)")
        print("  - carlos.lopez@empresa.com / tae123 (TAE)")
        print("")
        print("DATOS CREADOS:")
        print("  - 4 Departamentos")
        print("  - 3 Categorias de actividades (GRID, Soporte, Entrenamiento)")
        print(f"  - {len(templates)} Plantillas de actividades reales de TAE")
        print("  - 8 Tipos de emergencia")
        print("  - 6 Categorias de equipos")
        print("  - 7 Equipos (Ambulancias, SCBA, etc.)")
        print("  - 8 Tipos de certificacion")
        print("  - 8 Certificaciones de usuarios")
        print("  - 1 Plan mensual con 5 actividades")
        print("  - 3 Ejecuciones")
        print("  - 3 Emergencias")
        print("")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
