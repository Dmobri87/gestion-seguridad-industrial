"""
Script: add_coordinator_activities.py
Agrega columna coordinator_only a las tablas de categorías y plantillas,
e inserta las 4 categorías y 17 plantillas del plan de trabajo del coordinador.

Uso:
    docker compose exec backend python scripts/add_coordinator_activities.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import SessionLocal, engine


def run():
    db = SessionLocal()
    try:
        print("1. Agregando columna coordinator_only a activity_categories...")
        db.execute(text("""
            ALTER TABLE activity_categories
            ADD COLUMN IF NOT EXISTS coordinator_only BOOLEAN DEFAULT FALSE;
        """))

        print("2. Agregando columna coordinator_only a activity_templates...")
        db.execute(text("""
            ALTER TABLE activity_templates
            ADD COLUMN IF NOT EXISTS coordinator_only BOOLEAN DEFAULT FALSE;
        """))
        db.commit()
        print("   ✓ Columnas agregadas.")

        # ==========================================
        # CATEGORÍAS DEL COORDINADOR
        # ==========================================
        categories = [
            {
                "name": "VERIFICAR",
                "code": "COORD_VERIF",
                "description": "Actividades de verificación del coordinador",
                "display_order": 100,
                "color": "#52c41a",
                "icon": "CheckCircleOutlined",
                "coordinator_only": True,
            },
            {
                "name": "REALIZAR",
                "code": "COORD_REAL",
                "description": "Actividades operativas del coordinador",
                "display_order": 101,
                "color": "#1890ff",
                "icon": "PlayCircleOutlined",
                "coordinator_only": True,
            },
            {
                "name": "REVISA",
                "code": "COORD_REVIS",
                "description": "Actividades de revisión del coordinador",
                "display_order": 102,
                "color": "#722ed1",
                "icon": "EyeOutlined",
                "coordinator_only": True,
            },
            {
                "name": "OTROS",
                "code": "COORD_OTROS",
                "description": "Otras actividades del coordinador",
                "display_order": 103,
                "color": "#fa8c16",
                "icon": "AppstoreOutlined",
                "coordinator_only": True,
            },
        ]

        print("3. Insertando categorías del coordinador...")
        cat_ids = {}
        for cat in categories:
            # Verificar si ya existe
            result = db.execute(text(
                "SELECT id FROM activity_categories WHERE code = :code"
            ), {"code": cat["code"]}).fetchone()

            if result:
                cat_ids[cat["code"]] = result[0]
                print(f"   - {cat['name']} ya existe (id={result[0]}), omitiendo.")
                continue

            result = db.execute(text("""
                INSERT INTO activity_categories
                    (name, code, description, display_order, color, icon, coordinator_only, is_active)
                VALUES
                    (:name, :code, :description, :display_order, :color, :icon, :coordinator_only, TRUE)
                RETURNING id
            """), cat)
            cat_id = result.fetchone()[0]
            cat_ids[cat["code"]] = cat_id
            print(f"   ✓ {cat['name']} creada (id={cat_id})")

        db.commit()

        # ==========================================
        # PLANTILLAS POR CATEGORÍA
        # ==========================================
        templates = {
            "COORD_VERIF": [
                {"name": "Planes de Trabajo del TAE",                      "code": "CV-001", "order": 1, "requires_evidence": True},
                {"name": "Asistencia a Turno",                             "code": "CV-002", "order": 2, "requires_evidence": True},
                {"name": "Cumplimiento de Procesos",                       "code": "CV-003", "order": 3, "requires_evidence": True},
            ],
            "COORD_REAL": [
                {"name": "Recordación de riesgo en la conducción",         "code": "CR-001", "order": 1, "requires_evidence": True},
                {"name": "Recordación de riesgo en la atención de la emergencia", "code": "CR-002", "order": 2, "requires_evidence": True},
                {"name": "Visita de CAE",                                  "code": "CR-003", "order": 3, "requires_evidence": True},
                {"name": "Reunión diaria (G-COM)",                         "code": "CR-004", "order": 4, "requires_evidence": True},
                {"name": "Actualización de Nómina",                        "code": "CR-005", "order": 5, "requires_evidence": True},
                {"name": "Reportes de AL",                                 "code": "CR-006", "order": 6, "requires_evidence": True},
                {"name": "Seguimiento A&D",                                "code": "CR-007", "order": 7, "requires_evidence": True},
                {"name": "Soporte Inspección de Vías",                     "code": "CR-008", "order": 8, "requires_evidence": True},
                {"name": "Entrenamiento mensual",                          "code": "CR-009", "order": 9, "requires_evidence": True},
            ],
            "COORD_REVIS": [
                {"name": "Indicadores de Cumplimiento TAE",                "code": "CRV-001", "order": 1, "requires_evidence": True},
                {"name": "Cumplimiento de Actividades PSE",                "code": "CRV-002", "order": 2, "requires_evidence": True},
                {"name": "Avance PDI TAE",                                 "code": "CRV-003", "order": 3, "requires_evidence": True},
            ],
            "COORD_OTROS": [
                {"name": "Actividades PDI Propias",                        "code": "CO-001", "order": 1, "requires_evidence": True},
                {"name": "Creación herramientas digitales",                "code": "CO-002", "order": 2, "requires_evidence": False},
            ],
        }

        print("4. Insertando plantillas del coordinador...")
        total_inserted = 0
        for cat_code, tmpls in templates.items():
            cat_id = cat_ids.get(cat_code)
            if not cat_id:
                print(f"   ✗ No se encontró id para categoría {cat_code}, omitiendo.")
                continue

            for tmpl in tmpls:
                result = db.execute(text(
                    "SELECT id FROM activity_templates WHERE code = :code"
                ), {"code": tmpl["code"]}).fetchone()

                if result:
                    print(f"   - {tmpl['name']} ya existe, omitiendo.")
                    continue

                db.execute(text("""
                    INSERT INTO activity_templates
                        (name, code, category_id, display_order, requires_evidence,
                         coordinator_only, is_critical, default_frequency, is_active)
                    VALUES
                        (:name, :code, :category_id, :display_order, :requires_evidence,
                         TRUE, FALSE, 1, TRUE)
                """), {
                    "name": tmpl["name"],
                    "code": tmpl["code"],
                    "category_id": cat_id,
                    "display_order": tmpl["order"],
                    "requires_evidence": tmpl["requires_evidence"],
                })
                total_inserted += 1
                print(f"   ✓ {tmpl['name']}")

        db.commit()
        print(f"\n✅ Listo. {total_inserted} plantillas insertadas.")
        print("   Las categorías VERIFICAR, REALIZAR, REVISA y OTROS")
        print("   están disponibles exclusivamente para coordinadores.")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
