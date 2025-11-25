import sqlite3
import random
from datetime import datetime, timedelta

# Configuración
CANTIDAD_VENTAS = 3500
CANTIDAD_GASTOS = 300
DB_NAME = 'verduleria_final.db'

# Datos falsos para generar variedad
PRODUCTOS = [
    ("Papa Negra", "Kg"), ("Papa Blanca", "Kg"), ("Cebolla", "Kg"), ("Zanahoria", "Kg"),
    ("Zapallo Anco", "Kg"), ("Calabaza", "Kg"), ("Batata", "Kg"), ("Acelga", "Paquete"),
    ("Espinaca", "Paquete"), ("Lechuga Criolla", "Kg"), ("Lechuga Mantecosa", "Kg"),
    ("Tomate Perita", "Kg"), ("Tomate Redondo", "Kg"), ("Tomate Cherry", "Kg"),
    ("Morrón Rojo", "Kg"), ("Morrón Verde", "Kg"), ("Ajo", "Cabeza"), ("Perejil", "Atado"),
    ("Manzana Roja", "Kg"), ("Manzana Verde", "Kg"), ("Banana Ecuador", "Kg"),
    ("Banana Bolivia", "Kg"), ("Naranja Jugo", "Kg"), ("Naranja Ombligo", "Kg"),
    ("Mandarina", "Kg"), ("Pomelo", "Kg"), ("Limón", "Kg"), ("Pera", "Kg"),
    ("Uva Negra", "Kg"), ("Uva Blanca", "Kg"), ("Frutilla", "Kg"), ("Arándanos", "Cajita"),
    ("Kiwi", "Kg"), ("Palta Hass", "Unidad"), ("Huevo Blanco", "Maple"),
    ("Huevo Color", "Maple"), ("Miel", "Frasco"), ("Aceite de Oliva", "Botella")
]

PROVEEDORES = ["Mercado Central", "Quinta Los Hnos", "Distribuidora El Tano", "Flete Mario", "Luz del Local", "Alquiler", "Bolsas y Papel"]

MEDIOS_PAGO = ["Efectivo", "Efectivo", "Efectivo", "Efectivo", "Mercado Pago", "Mercado Pago", "Mercado Pago", "Débito", "Crédito"]

def generar_fecha_random():
    """Genera una fecha aleatoria en el último año"""
    dias_atras = random.randint(0, 365)
    fecha_base = datetime.now() - timedelta(days=dias_atras)
    # Hora aleatoria entre 08:00 y 20:00
    hora = random.randint(8, 20)
    minuto = random.randint(0, 59)
    segundo = random.randint(0, 59)
    return fecha_base.replace(hour=hora, minute=minuto, second=segundo).strftime("%Y-%m-%d %H:%M:%S")

def poblar_db():
    print(f"conectando a {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1. Limpiar datos viejos (Opcional: Si querés sumar en vez de borrar, comentá estas líneas)
    print("Limpiando tablas antiguas...")
    c.execute("DELETE FROM ventas")
    c.execute("DELETE FROM gastos")
    c.execute("DELETE FROM stock")
    
    # 2. Generar Stock
    print("Generando Stock...")
    for prod, unidad in PRODUCTOS:
        cantidad = round(random.uniform(0.5, 50.0), 2) # Entre 0.5 y 50 unidades/kg
        c.execute("INSERT INTO stock (producto, cantidad, unidad) VALUES (?, ?, ?)", (prod, cantidad, unidad))

    # 3. Generar Ventas
    print(f"Generando {CANTIDAD_VENTAS} ventas (esto puede tardar unos segundos)...")
    ventas_data = []
    for _ in range(CANTIDAD_VENTAS):
        fecha = generar_fecha_random()
        medio = random.choice(MEDIOS_PAGO)
        
        monto = round(random.uniform(1500, 18000), -2)
        if random.random() < 0.2:
             monto += 50

        # CAMBIO AQUÍ: Eliminamos el "if random < 0.3"
        # Ahora SIEMPRE genera un DNI entre 20 y 45 millones
        dni = str(random.randint(20000000, 45000000))
        
        ventas_data.append((fecha, dni, medio, monto))
    
    c.executemany("INSERT INTO ventas (fecha, dni, medio_pago, monto) VALUES (?, ?, ?, ?)", ventas_data)

    # 4. Generar Gastos
    print(f"Generando {CANTIDAD_GASTOS} gastos...")
    gastos_data = []
    for _ in range(CANTIDAD_GASTOS):
        fecha = generar_fecha_random()
        desc = random.choice(PROVEEDORES)
        monto = round(random.uniform(10000, 150000), 2)
        gastos_data.append((fecha, desc, monto))
        
    c.executemany("INSERT INTO gastos (fecha, descripcion, monto) VALUES (?, ?, ?)", gastos_data)

    conn.commit()
    conn.close()
    print("¡Listo! Base de datos cargada exitosamente.")

if __name__ == "__main__":
    poblar_db()