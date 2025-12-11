import sqlite3
import pandas as pd
import hashlib

DB_NAME = "dental_hada_tesis.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Tabla Odontologos
    c.execute('''CREATE TABLE IF NOT EXISTS Odontologos (
        id_odontologo INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL, password TEXT NOT NULL, nombre_completo TEXT)''')
    
    # 2. Tabla Pacientes
    c.execute('''CREATE TABLE IF NOT EXISTS Pacientes (
        id_paciente INTEGER PRIMARY KEY AUTOINCREMENT,
        nombres TEXT NOT NULL, apellidos TEXT NOT NULL, dni TEXT UNIQUE, fecha_nacimiento DATE)''')
    
    # 3. Tabla Radiografias
    c.execute('''CREATE TABLE IF NOT EXISTS Radiografias (
        id_radiografia INTEGER PRIMARY KEY AUTOINCREMENT,
        id_paciente INTEGER NOT NULL, id_odontologo_carga INTEGER,
        ruta_archivo TEXT, fecha_toma DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_paciente) REFERENCES Pacientes(id_paciente),
        FOREIGN KEY (id_odontologo_carga) REFERENCES Odontologos(id_odontologo))''')
    
    # 4. Tabla Resultados IA
    c.execute('''CREATE TABLE IF NOT EXISTS Analisis_IA (
        id_analisis INTEGER PRIMARY KEY AUTOINCREMENT, id_radiografia INTEGER NOT NULL,
        version_modelo TEXT DEFAULT 'U-Net ResNet50 HD', tiempo_analisis_ms REAL,
        conteo_lesiones_ia INTEGER, conteo_real INTEGER, errores INTEGER, precision REAL, json_mascara_ia TEXT,
        FOREIGN KEY (id_radiografia) REFERENCES Radiografias(id_radiografia))''')
    
    # Usuario Admin por defecto
    try:
        pass_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO Odontologos (id_odontologo, usuario, password, nombre_completo) VALUES (1, 'admin', ?, 'Administrador Hada')", (pass_hash,))
    except: pass
    conn.commit()
    conn.close()

def verificar_login(usuario, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    pass_hash = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT id_odontologo, nombre_completo FROM Odontologos WHERE usuario=? AND password=?", (usuario, pass_hash))
    user = c.fetchone()
    conn.close()
    return user

def registrar_paciente(nombres, apellidos, dni):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO Pacientes (nombres, apellidos, dni) VALUES (?, ?, ?)", (nombres, apellidos, dni))
    conn.commit()
    conn.close()

def obtener_pacientes():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id_paciente, nombres || ' ' || apellidos as nombre_completo FROM Pacientes", conn)
    conn.close()
    return df

def obtener_historial_visual(id_paciente):
    conn = sqlite3.connect(DB_NAME)
    query = '''
        SELECT r.fecha_toma, r.ruta_archivo, a.conteo_lesiones_ia, a.conteo_real, a.precision, a.errores, a.tiempo_analisis_ms
        FROM Radiografias r
        LEFT JOIN Analisis_IA a ON r.id_radiografia = a.id_radiografia
        WHERE r.id_paciente = ? ORDER BY r.fecha_toma DESC
    '''
    df = pd.read_sql_query(query, conn, params=(id_paciente,))
    conn.close()
    return df

def obtener_metricas_globales():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM Analisis_IA", conn)
    conn.close()
    return df

def guardar_analisis_completo(id_paciente, id_odontologo, ruta_final, tiempo, ia, real, error, prec):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO Radiografias (id_paciente, id_odontologo_carga, ruta_archivo) VALUES (?, ?, ?)",
              (id_paciente, id_odontologo, ruta_final))
    id_rad = c.lastrowid
    c.execute('''INSERT INTO Analisis_IA (id_radiografia, tiempo_analisis_ms, conteo_lesiones_ia, conteo_real, errores, precision)
        VALUES (?, ?, ?, ?, ?, ?)''', (id_rad, tiempo, ia, real, error, prec))
    conn.commit()
    conn.close()