import sqlite3
import os

# --- CONFIGURACIÓN ---
OLD_DB_PATH = 'instance/OLD_wfm.db'  
NEW_DB_PATH = 'instance/wfm.db'      

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def migrate():
    if not os.path.exists(OLD_DB_PATH):
        print(f"Error: No se encuentra la base de datos vieja en {OLD_DB_PATH}")
        return
    if not os.path.exists(NEW_DB_PATH):
        print(f"Error: No se encuentra la base de datos nueva en {NEW_DB_PATH}")
        return

    print(">>> Iniciando migración de datos...")

    con_old = sqlite3.connect(OLD_DB_PATH)
    con_old.row_factory = dict_factory
    cur_old = con_old.cursor()

    con_new = sqlite3.connect(NEW_DB_PATH)
    # Para la nueva también usamos diccionario para facilitar lecturas intermedias
    con_new.row_factory = dict_factory 
    cur_new = con_new.cursor()

    # --- 1. MIGRAR USUARIOS ---
    print("- Migrando Usuarios...")
    users = cur_old.execute("SELECT * FROM user").fetchall()
    for u in users:
        keys = ', '.join(u.keys())
        placeholders = ', '.join(['?'] * len(u))
        cur_new.execute(f"INSERT OR IGNORE INTO user ({keys}) VALUES ({placeholders})", list(u.values()))

    # --- 2. MIGRAR CAMPAÑAS ---
    print("- Migrando Campañas...")
    campaigns = cur_old.execute("SELECT * FROM campaign").fetchall()
    for c in campaigns:
        keys = ', '.join(c.keys())
        placeholders = ', '.join(['?'] * len(c))
        cur_new.execute(f"INSERT OR IGNORE INTO campaign ({keys}) VALUES ({placeholders})", list(c.values()))

    # --- 3. MIGRAR SEGMENTOS ---
    print("- Migrando Segmentos...")
    segments = cur_old.execute("SELECT * FROM segment").fetchall()
    for s in segments:
        s['required_skills'] = None 
        keys = ', '.join(s.keys())
        placeholders = ', '.join(['?'] * len(s))
        cur_new.execute(f"INSERT OR IGNORE INTO segments ({keys}) VALUES ({placeholders})", list(s.values()))

    # --- 4. MIGRAR REGLAS ---
    print("- Migrando Reglas de Contrato...")
    try:
        rules = cur_old.execute("SELECT * FROM scheduling_rule").fetchall()
    except sqlite3.OperationalError:
        rules = cur_old.execute("SELECT * FROM scheduling_rules").fetchall()
        
    for r in rules:
        keys = ', '.join(r.keys())
        placeholders = ', '.join(['?'] * len(r))
        cur_new.execute(f"INSERT OR IGNORE INTO scheduling_rules ({keys}) VALUES ({placeholders})", list(r.values()))

    # --- 5. MIGRAR AGENTES (CON CORRECCIÓN DE ERROR) ---
    print("- Migrando Agentes...")
    
    # Buscar una regla por defecto (la primera que exista) para asignar a los huérfanos
    default_rule = cur_new.execute("SELECT id FROM scheduling_rules LIMIT 1").fetchone()
    default_rule_id = default_rule['id'] if default_rule else 1
    
    agents = cur_old.execute("SELECT * FROM agent").fetchall()
    for a in agents:
        a['skill'] = 'INBOUND'
        
        # CORRECCIÓN: Si no tiene regla, asignamos la por defecto
        if a['scheduling_rule_id'] is None:
            print(f"  > Aviso: Agente '{a['nombre_completo']}' no tenía regla. Asignando ID {default_rule_id}.")
            a['scheduling_rule_id'] = default_rule_id
        
        keys = ', '.join(a.keys())
        placeholders = ', '.join(['?'] * len(a))
        cur_new.execute(f"INSERT OR IGNORE INTO agents ({keys}) VALUES ({placeholders})", list(a.values()))

    # --- 6. MIGRAR STAFFING ---
    print("- Migrando Forecast (Staffing)...")
    staffing = cur_old.execute("SELECT * FROM staffing_result").fetchall()
    for st in staffing:
        keys = ', '.join(st.keys())
        placeholders = ', '.join(['?'] * len(st))
        cur_new.execute(f"INSERT OR IGNORE INTO staffing_results ({keys}) VALUES ({placeholders})", list(st.values()))

    # --- 7. MIGRAR HORARIOS ---
    print("- Migrando Horarios...")
    schedules = cur_old.execute("SELECT * FROM schedule").fetchall()
    for sch in schedules:
        keys = ', '.join(sch.keys())
        placeholders = ', '.join(['?'] * len(sch))
        cur_new.execute(f"INSERT OR IGNORE INTO schedules ({keys}) VALUES ({placeholders})", list(sch.values()))
        
    # --- 8. OTROS ---
    print("- Migrando Datos Históricos...")
    try:
        actuals = cur_old.execute("SELECT * FROM actuals_data").fetchall()
        for act in actuals:
            keys = ', '.join(act.keys())
            placeholders = ', '.join(['?'] * len(act))
            cur_new.execute(f"INSERT OR IGNORE INTO actuals_data ({keys}) VALUES ({placeholders})", list(act.values()))
    except: pass

    try:
        monthly = cur_old.execute("SELECT * FROM monthly_forecast").fetchall()
        for m in monthly:
            keys = ', '.join(m.keys())
            placeholders = ', '.join(['?'] * len(m))
            cur_new.execute(f"INSERT OR IGNORE INTO monthly_forecasts ({keys}) VALUES ({placeholders})", list(m.values()))
    except: pass

    con_new.commit()
    con_old.close()
    con_new.close()
    print("\n>>> ¡MIGRACIÓN COMPLETADA! <<<")

if __name__ == '__main__':
    migrate()