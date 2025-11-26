import sqlite3
import random
from datetime import datetime, timedelta, time

# === CONFIGURACIÓN ===
DB_NAME = 'verduleria_final.db'
CANTIDAD_VENTAS = 4200  # Unas 10-15 ventas por día promedio en el año
ANIO = 2025

# === PRECIOS BASE 2025 (Estimados para cálculo de ticket) ===
# Estos precios son una referencia para armar tickets coherentes
# Se les aplicará inflación según el mes del año.
PRECIOS_REF = {
    "Papa": 1200, "Cebolla": 1500, "Zanahoria": 1100, "Calabaza": 900,
    "Tomate": 3500, "Lechuga": 4000, "Acelga": 1500, "Morron": 6500,
    "Banana": 2800, "Manzana": 3200, "Naranja": 2200, "Palta": 5500,
    "Frutilla": 6000, "Huevos": 4500, "Limon": 1800
}

# === STOCK INICIAL (Lo que tenés en el depósito hoy) ===
STOCK_INICIAL = [
    ("Papa Negra", 250, "Kg"), ("Papa Blanca", 100, "Kg"), ("Cebolla", 120, "Kg"), 
    ("Zanahoria", 40, "Kg"), ("Zapallo Anco", 60, "Kg"), ("Cabutia", 30, "Kg"),
    ("Acelga", 15, "Atado"), ("Espinaca", 10, "Atado"), ("Lechuga Criolla", 12, "Kg"),
    ("Lechuga Mantecosa", 8, "Kg"), ("Tomate Perita", 45, "Kg"), ("Tomate Redondo", 30, "Kg"),
    ("Tomate Cherry", 20, "Kg"), ("Morrón Rojo", 15, "Kg"), ("Morrón Verde", 20, "Kg"),
    ("Ajo", 50, "Cabeza"), ("Perejil", 30, "Atado"), ("Manzana Roja", 40, "Kg"),
    ("Manzana Verde", 35, "Kg"), ("Banana Ecuador", 60, "Kg"), ("Banana Bolivia", 80, "Kg"),
    ("Naranja Jugo", 100, "Kg"), ("Naranja Ombligo", 50, "Kg"), ("Mandarina", 40, "Kg"),
    ("Pomelo", 20, "Kg"), ("Limón", 30, "Kg"), ("Pera", 25, "Kg"),
    ("Palta Hass", 18, "Unidad"), ("Huevo Blanco", 40, "Maple"), ("Huevo Color", 20, "Maple"),
    ("Miel Pura", 10, "Frasco"), ("Aceite Oliva", 5, "Botella")
]

PROVEEDORES = ["Mercado Central", "Quinta Los Hnos", "Distribuidora El Tano", "Flete Mario", "Luz EPEC/Edenor", "Alquiler Local", "Bolsas y Empaques"]
MEDIOS_PAGO = ["Efectivo", "Efectivo", "Efectivo", "Mercado Pago", "Mercado Pago", "Débito", "Crédito"]

def generar_fecha_hora_realista():
    """
    Genera una fecha de 2025 respetando horarios comerciales y días pico.
    """
    start_date = datetime(ANIO, 1, 1)
    # Asumimos que hoy es fines de Noviembre 2025 para la simulación
    end_date = datetime(ANIO, 11, 25) 
    
    delta_days = (end_date - start_date).days
    
    while True:
        # Elegir día al azar
        random_day = random.randint(0, delta_days)
        fecha = start_date + timedelta(days=random_day)
        dia_semana = fecha.weekday() # 0=Lunes, 6=Domingo
        
        # PONDERACIÓN POR DÍA DE SEMANA
        # Domingo (6): Cerrado o mediodía -> Pocas probabilidades
        if dia_semana == 6 and random.random() > 0.1: continue 
        # Lunes (0): Día flojo -> 30% chance de rechazar venta simulada
        if dia_semana == 0 and random.random() > 0.3: continue
        # Viernes(4) y Sábado(5): Días fuertes -> Pasan casi siempre
        
        # PONDERACIÓN HORARIA (Simulando picos)
        hora = random.randint(9, 20) # Abierto de 9 a 21
        minuto = random.randint(0, 59)
        
        # Siesta (14 a 16hs): Baja venta
        if 14 <= hora <= 16:
            if random.random() > 0.2: continue # 80% chance de que NO haya nadie a la siesta
            
        fecha_final = fecha.replace(hour=hora, minute=minuto, second=random.randint(0,59))
        return fecha_final

def calcular_monto_ticket(fecha):
    """
    Simula una compra de varios productos y aplica inflación según el mes.
    """
    # 1. Simular canasta (cuántas cosas lleva la gente)
    cant_items = random.randint(1, 8) # Llevan entre 1 y 8 tipos de cosas
    if random.random() < 0.1: cant_items = random.randint(10, 20) # 10% son compras grandes mensuales
    
    total_base = 0
    items_disponibles = list(PRECIOS_REF.values())
    
    for _ in range(cant_items):
        # Elige un precio base y suma cantidad (ej: 1.5kg de algo)
        precio_item = random.choice(items_disponibles)
        cantidad = random.uniform(0.5, 2.0)
        total_base += precio_item * cantidad
        
    # 2. Aplicar INFLACIÓN PROGRESIVA 2025
    # Asumimos 4% mensual acumulativo aprox
    mes = fecha.month
    inflacion = (1.04) ** (mes - 1) 
    
    monto_final = total_base * inflacion
    
    # Redondeo "de verdulero" (a $10 o $50)
    return round(monto_final / 10) * 10

def poblar_db():
    print(f"--- INICIANDO SIMULACIÓN VERDULERÍA {ANIO} ---")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1. Limpieza
    print("🧹 Limpiando base de datos anterior...")
    c.execute("DELETE FROM ventas")
    c.execute("DELETE FROM gastos")
    c.execute("DELETE FROM stock")
    
    # 2. Cargar Stock
    print("📦 Llenando las estanterías (Stock)...")
    c.executemany("INSERT INTO stock (producto, cantidad, unidad) VALUES (?, ?, ?)", STOCK_INICIAL)

    # 3. Generar Ventas
    print(f"💰 Simulando {CANTIDAD_VENTAS} ventas a lo largo del año...")
    ventas_data = []
    
    for _ in range(CANTIDAD_VENTAS):
        fecha = generar_fecha_hora_realista()
        monto = calcular_monto_ticket(fecha)
        medio = random.choice(MEDIOS_PAGO)
        
        # DNI Obligatorio
        dni = str(random.randint(20000000, 46000000))
        
        # Formato fecha string para SQLite
        fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S")
        ventas_data.append((fecha_str, dni, medio, monto))
    
    # Ordenamos las ventas por fecha para que queden prolijas en la DB
    ventas_data.sort(key=lambda x: x[0])
    
    c.executemany("INSERT INTO ventas (fecha, dni, medio_pago, monto) VALUES (?, ?, ?, ?)", ventas_data)

    # 4. Generar Gastos (Alquiler, Luz, Mercadería)
    print("📉 Generando gastos operativos...")
    gastos_data = []
    fecha_cursor = datetime(ANIO, 1, 5)
    
    while fecha_cursor < datetime(ANIO, 11, 25):
        # Gasto Semanal: Reposición Mercadería (Mercado Central)
        costo_mercaderia = random.uniform(300000, 800000) * ((1.04) ** (fecha_cursor.month - 1))
        gastos_data.append((fecha_cursor.strftime("%Y-%m-%d 06:00:00"), "Reposición Mercado Central", round(costo_mercaderia, 2)))
        
        # Gasto Mensual: Alquiler (Día 10)
        if fecha_cursor.day == 10:
            alquiler = 450000 * ((1.02) ** (fecha_cursor.month - 1)) # Alquiler sube menos frec
            gastos_data.append((fecha_cursor.strftime("%Y-%m-%d 09:00:00"), "Alquiler Local", round(alquiler, 2)))
            
        # Gasto Mensual: Luz (Día 20)
        if fecha_cursor.day == 20:
            luz = random.uniform(80000, 150000) * ((1.05) ** (fecha_cursor.month - 1)) # La luz sube más
            gastos_data.append((fecha_cursor.strftime("%Y-%m-%d 10:00:00"), "Luz Comercial", round(luz, 2)))

        fecha_cursor += timedelta(days=random.randint(3, 7)) # Avanzar unos días

    c.executemany("INSERT INTO gastos (fecha, descripcion, monto) VALUES (?, ?, ?)", gastos_data)

    conn.commit()
    conn.close()
    print("✅ ¡LISTO! Tu verdulería ya tiene historia completa de 2025.")

if __name__ == "__main__":
    poblar_db()