from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class EquipmentStatus(str, enum.Enum):
    """Estados de equipo"""
    OPERATIONAL = "Operativo"
    IN_MAINTENANCE = "En Mantenimiento"
    OUT_OF_SERVICE = "Fuera de Servicio"
    RETIRED = "Dado de Baja"


class MaintenanceType(str, enum.Enum):
    """Tipos de mantenimiento"""
    PREVENTIVE = "Preventivo"
    CORRECTIVE = "Correctivo"
    EMERGENCY = "Emergencia"


class EquipmentCategory(Base):
    """
    Categorías de equipos.
    Ej: Ambulancias, SCBA, Radios, Bombas CI, etc.
    """
    __tablename__ = "equipment_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Configuración de mantenimiento
    default_maintenance_frequency_days = Column(Integer, default=30)  # días

    # Icono y color para UI
    icon = Column(String(50), nullable=True)
    color = Column(String(20), default="#1890ff")

    # Orden de visualización
    display_order = Column(Integer, default=0)

    # Estado
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    equipment_list = relationship("Equipment", back_populates="category")


class Equipment(Base):
    """
    Inventario de equipos de seguridad.
    """
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)

    # Categoría
    category_id = Column(Integer, ForeignKey("equipment_categories.id"), nullable=False)
    category = relationship("EquipmentCategory", back_populates="equipment_list")

    # Identificación
    code = Column(String(50), unique=True, nullable=False, index=True)  # AMB-001, SCBA-002
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Datos del equipo
    brand = Column(String(100), nullable=True)  # Marca
    model = Column(String(100), nullable=True)  # Modelo
    serial_number = Column(String(100), nullable=True, unique=True)  # Número de serie
    year = Column(Integer, nullable=True)  # Año de fabricación

    # Fechas importantes
    purchase_date = Column(Date, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    last_maintenance_date = Column(Date, nullable=True)
    next_maintenance_date = Column(Date, nullable=True)

    # Estado
    status = Column(String(50), default=EquipmentStatus.OPERATIONAL.value)

    # Disponibilidad por turno
    is_available_day = Column(Boolean, default=True)    # Turno diurno (06:00-18:00)
    is_available_night = Column(Boolean, default=True)  # Turno nocturno (18:00-06:00)

    # Ubicación
    location = Column(String(255), nullable=True)  # CAE asignado
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    # Responsable
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Valor
    purchase_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)

    # Configuración de mantenimiento
    maintenance_frequency_days = Column(Integer, nullable=True)

    # Inventario
    quantity = Column(Integer, default=1)
    min_stock = Column(Integer, default=1)

    # Notas
    notes = Column(Text, nullable=True)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Estado activo
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    maintenances = relationship("EquipmentMaintenance", back_populates="equipment", cascade="all, delete-orphan")
    inspections = relationship("EquipmentInspection", back_populates="equipment", cascade="all, delete-orphan")
    files = relationship("EquipmentFile", back_populates="equipment", cascade="all, delete-orphan")
    novelties = relationship("EquipmentNovelty", back_populates="equipment", cascade="all, delete-orphan")


class EquipmentMaintenance(Base):
    """
    Registro de mantenimientos de equipos.
    """
    __tablename__ = "equipment_maintenances"

    id = Column(Integer, primary_key=True, index=True)

    # Equipo
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    equipment = relationship("Equipment", back_populates="maintenances")

    # Tipo de mantenimiento
    maintenance_type = Column(String(50), default=MaintenanceType.PREVENTIVE.value)

    # Fechas
    scheduled_date = Column(Date, nullable=False)
    completed_date = Column(Date, nullable=True)

    # Descripción
    description = Column(Text, nullable=True)
    work_performed = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)

    # Proveedor/técnico
    technician = Column(String(255), nullable=True)
    provider = Column(String(255), nullable=True)

    # Costos
    labor_cost = Column(Float, nullable=True)
    parts_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)

    # Estado
    status = Column(String(50), default="Programado")  # Programado, En Proceso, Completado, Cancelado

    # Realizado por
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EquipmentInspection(Base):
    """
    Registro de inspecciones de equipos.
    """
    __tablename__ = "equipment_inspections"

    id = Column(Integer, primary_key=True, index=True)

    # Equipo
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    equipment = relationship("Equipment", back_populates="inspections")

    # Fecha de inspección
    inspection_date = Column(Date, nullable=False)

    # Resultado
    result = Column(String(50), nullable=False)  # Aprobado, Rechazado, Con Observaciones
    observations = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)

    # Checklist completado (JSON)
    checklist_data = Column(Text, nullable=True)

    # Inspector
    inspected_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Próxima inspección
    next_inspection_date = Column(Date, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EquipmentFile(Base):
    """
    Archivos adjuntos a equipos (manuales, fotos, certificados).
    """
    __tablename__ = "equipment_files"

    id = Column(Integer, primary_key=True, index=True)

    # Equipo
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    equipment = relationship("Equipment", back_populates="files")

    # Tipo de documento
    document_type = Column(String(100), nullable=False)  # Manual, Certificado, Foto, etc.

    # Información del archivo
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_url = Column(String(500), nullable=False)

    # Descripción
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)


class EquipmentNovelty(Base):
    """
    Registro de novedades de equipos (indisponibilidad, salida de servicio, etc.).
    Cada vez que un equipo sale de servicio o tiene una novedad, se registra aquí.
    """
    __tablename__ = "equipment_novelties"

    id = Column(Integer, primary_key=True, index=True)

    # Equipo
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    equipment = relationship("Equipment", back_populates="novelties")

    # Tipo de novedad
    novelty_type = Column(String(50), nullable=False)  # Fuera de Servicio, En Mantenimiento, Siniestro, Otro

    # Descripción de la novedad
    description = Column(Text, nullable=False)

    # Turno afectado
    shift = Column(String(20), nullable=False)  # Día, Noche, Ambos

    # Horas de indisponibilidad
    unavailable_hours = Column(Float, default=0)  # Horas fuera de servicio en este evento

    # Fechas
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)  # NULL = aún fuera de servicio
    is_resolved = Column(Boolean, default=False)

    # Resolución
    resolution = Column(Text, nullable=True)

    # Estado previo del equipo (para restaurar al resolver)
    previous_status = Column(String(50), nullable=True)

    # Usuario que registró
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
