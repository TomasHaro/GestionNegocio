import sqlite3

DB_NAME = 'verduleria_final.db'

def inicializar_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, dni TEXT, medio_pago TEXT, monto REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS gastos (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, descripcion TEXT, monto REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, producto TEXT, cantidad REAL, unidad TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (dni TEXT PRIMARY KEY, nombre TEXT, saldo REAL)''')
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_NAME)