import cargar_datos_prueba
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
from datetime import datetime
import pandas as pd
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

class VerduleriaFinal:
    def __init__(self, root):
        self.root = root
        self.root.title("Verdulería - Caja Rápida y Stock")
        self.root.geometry("1100x700") 
        
        self.crear_base_datos()
        
        # Sistema de Pestañas
        self.notebook = ttk.Notebook(self.root, bootstyle="primary")
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        self.frame_caja = ttk.Frame(self.notebook)
        self.frame_stock = ttk.Frame(self.notebook)
        self.frame_balance = ttk.Frame(self.notebook)
        self.frame_reportes = ttk.Frame(self.notebook) # <--- NUEVA LÍNEA

        self.notebook.add(self.frame_caja, text="⚡ CAJA RÁPIDA")
        self.notebook.add(self.frame_stock, text="📦 STOCK")
        self.notebook.add(self.frame_balance, text="💰 CIERRE")
        self.notebook.add(self.frame_reportes, text="📊 REPORTES PDF") # <--- NUEVA LÍNEA

        self.setup_caja()
        self.setup_stock()
        self.setup_balance()
        self.setup_reportes()

        self.root.after(500, self.verificar_datos_prueba)

    def crear_base_datos(self):
        conn = sqlite3.connect('verduleria_final.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, dni TEXT, medio_pago TEXT, monto REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS gastos (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, descripcion TEXT, monto REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, producto TEXT, cantidad REAL, unidad TEXT)''')
        conn.commit()
        conn.close()

    # ==========================================
    # PESTAÑA 1: CAJA RÁPIDA (SOLO MONTO)
    # ==========================================
    def setup_caja(self):
        # --- LADO IZQUIERDO: COBRO ---
        izq = ttk.Labelframe(self.frame_caja, text=" Nueva Venta ", padding=20, bootstyle="info", width=400)
        izq.pack(side="left", fill="y", padx=10, pady=10)
        izq.pack_propagate(False)

        # 1. Monto
        ttk.Label(izq, text="MONTO A COBRAR ($):", font=("Arial", 12, "bold")).pack(anchor="w")
        self.entry_monto = ttk.Entry(izq, font=("Arial", 24))
        self.entry_monto.pack(fill="x", pady=(5, 20))
        self.entry_monto.bind('<Return>', lambda e: self.registrar_venta()) 
        self.entry_monto.focus()

        # 2. Medio de Pago
        ttk.Label(izq, text="Medio de Pago:").pack(anchor="w")
        self.combo_pago = ttk.Combobox(izq, values=["Efectivo", "Mercado Pago", "Débito", "Crédito"], state="readonly", font=("Arial", 12))
        self.combo_pago.current(0)
        self.combo_pago.pack(fill="x", pady=(5, 15))

        # 3. DNI
        ttk.Label(izq, text="DNI Cliente (OBLIGATORIO):").pack(anchor="w")
        
        # --- REGISTRO DE VALIDACIÓN ---
        # Registramos la función en tcl/tk para que pueda usarla el widget
        vcmd = (self.root.register(self.validar_solo_numeros), '%P')
        
        # Agregamos validate="key" (valida cada tecla) y validatecommand=vcmd
        self.entry_dni = ttk.Entry(izq, font=("Arial", 12), validate="key", validatecommand=vcmd)
        
        self.entry_dni.pack(fill="x", pady=(5, 20))

        # Botones
        btn_cobrar = ttk.Button(izq, text="CONFIRMAR VENTA (Enter)", bootstyle="success", command=self.registrar_venta)
        btn_cobrar.pack(fill="x", ipady=10)

        ttk.Separator(izq, orient='horizontal').pack(fill='x', pady=20)
        
        ttk.Button(izq, text="🛑 REGISTRAR GASTO", bootstyle="danger", command=self.registrar_gasto).pack(fill="x")

        # --- LADO DERECHO: LISTA ---
        der = ttk.Frame(self.frame_caja, padding=10)
        der.pack(side="right", fill="both", expand=True)
        
        ttk.Label(der, text="Últimos Movimientos", font=("Arial", 12, "bold")).pack(anchor="w")
        
        cols = ("Hora", "Tipo", "Detalle/DNI", "Monto")
        self.tree_mov = ttk.Treeview(der, columns=cols, show="headings", bootstyle="primary")
        self.tree_mov.heading("Hora", text="Hora"); self.tree_mov.column("Hora", width=80)
        self.tree_mov.heading("Tipo", text="Tipo"); self.tree_mov.column("Tipo", width=80)
        self.tree_mov.heading("Detalle/DNI", text="Detalle / DNI"); self.tree_mov.column("Detalle/DNI", width=150)
        self.tree_mov.heading("Monto", text="Monto"); self.tree_mov.column("Monto", width=100)
        self.tree_mov.pack(fill="both", expand=True)
        
        # Configuración de colores de la tabla (AQUÍ ESTÁ EL CAMBIO)
        # Usamos colores HEX brillantes para que se vean sobre fondo oscuro
        self.tree_mov.tag_configure("g", foreground="#ff8a80") # Rojo Pastel Brillante
        self.tree_mov.tag_configure("v", foreground="#00e676") # Verde Neon Brillante
        
        self.cargar_movimientos()

    def registrar_venta(self):
        dni = self.entry_dni.get().strip()
    
        if not dni:
            messagebox.showwarning("Falta DNI", "🛑 El campo DNI es OBLIGATORIO.\nNo se puede registrar la venta sin identificar al cliente.")
            self.entry_dni.focus() # Ponemos el cursor ahí para que escriba
            return # <--- ACÁ SE CORTA LA FUNCIÓN

        if len(dni) < 7: # Validación extra por si puso un DNI muy corto
             messagebox.showwarning("Error", "El DNI parece incompleto (mínimo 7 números).")
             self.entry_dni.focus()
             return
        
        try:
            monto = float(self.entry_monto.get())
            if monto <= 0: raise ValueError
        except:
            messagebox.showerror("Error", "Ingresa un monto válido.")
            return

        conn = sqlite3.connect('verduleria_final.db')
        conn.execute("INSERT INTO ventas (fecha, dni, medio_pago, monto) VALUES (?, ?, ?, ?)",
                     (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.entry_dni.get(), self.combo_pago.get(), monto))
        conn.commit(); conn.close()
        
        self.generar_ticket_texto(monto, self.entry_dni.get(), self.combo_pago.get())

        self.entry_monto.delete(0, tk.END)
        self.entry_dni.delete(0, tk.END)
        self.cargar_movimientos()
        self.actualizar_graficos() 
        self.entry_monto.focus()

    def registrar_gasto(self):
        # Agregamos parent=self.root para obligar a la ventana a salir encima de la app
        desc = simpledialog.askstring("Gasto", "Descripción (Ej: Proveedor Papas):", parent=self.root)
        
        if desc:
            # A veces ayuda forzar una actualización visual pequeña antes del segundo
            self.root.update() 
            
            # También aquí agregamos parent=self.root
            monto = simpledialog.askfloat("Gasto", "Monto ($):", parent=self.root)
            
            if monto:
                conn = sqlite3.connect('verduleria_final.db')
                conn.execute("INSERT INTO gastos (fecha, descripcion, monto) VALUES (?, ?, ?)", 
                             (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), desc, monto))
                conn.commit(); conn.close()
                self.cargar_movimientos()
                self.actualizar_graficos()

    def cargar_movimientos(self):
        for i in self.tree_mov.get_children(): self.tree_mov.delete(i)
        conn = sqlite3.connect('verduleria_final.db')
        hoy = datetime.now().strftime("%Y-%m-%d")
        
        ventas = [("VENTA", r[0], r[1] if r[1] else "Consumidor Final", r[2]) for r in conn.execute("SELECT fecha, dni, monto FROM ventas WHERE fecha LIKE ?", (f'{hoy}%',))]
        gastos = [("GASTO", r[0], r[1], r[2] * -1) for r in conn.execute("SELECT fecha, descripcion, monto FROM gastos WHERE fecha LIKE ?", (f'{hoy}%',))]
        
        todos = sorted(ventas + gastos, key=lambda x: x[1], reverse=True)
        for tipo, fecha, det, monto in todos:
            hora = fecha.split(" ")[1][:5]
            tag = "g" if tipo == "GASTO" else "v"
            self.tree_mov.insert("", tk.END, values=(hora, tipo, det, f"${monto:,.2f}"), tags=(tag,))
        
        conn.close()

    # ==========================================
    # PESTAÑA 2: CONTROL DE STOCK
    # ==========================================
    def setup_stock(self):
        top = ttk.Frame(self.frame_stock, padding=10)
        top.pack(fill="x")
        
        ttk.Label(top, text="Producto:").pack(side="left")
        self.ent_stock_prod = ttk.Entry(top, width=20); self.ent_stock_prod.pack(side="left", padx=5)
        
        ttk.Label(top, text="Cantidad:").pack(side="left")
        self.ent_stock_cant = ttk.Entry(top, width=10); self.ent_stock_cant.pack(side="left", padx=5)

        ttk.Label(top, text="Unidad:").pack(side="left")
        self.combo_unidad = ttk.Combobox(top, values=["Kg", "Unidad", "Bolsa", "Cajón"], width=10); self.combo_unidad.current(0)
        self.combo_unidad.pack(side="left", padx=5)
        
        ttk.Button(top, text="Guardar", command=self.guardar_stock).pack(side="left", padx=10)

        self.tree_stock = ttk.Treeview(self.frame_stock, columns=("Producto", "Cantidad", "Unidad"), show="headings", bootstyle="primary")
        self.tree_stock.heading("Producto", text="Producto"); self.tree_stock.heading("Cantidad", text="Cantidad Actual"); self.tree_stock.heading("Unidad", text="Unidad")
        self.tree_stock.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.cargar_stock()

    def guardar_stock(self):
        prod = self.ent_stock_prod.get()
        cant = self.ent_stock_cant.get()
        unidad = self.combo_unidad.get()
        
        if prod and cant:
            conn = sqlite3.connect('verduleria_final.db')
            cursor = conn.execute("SELECT id FROM stock WHERE producto = ?", (prod,))
            data = cursor.fetchone()
            if data: conn.execute("UPDATE stock SET cantidad = ?, unidad = ? WHERE id = ?", (cant, unidad, data[0]))
            else: conn.execute("INSERT INTO stock (producto, cantidad, unidad) VALUES (?, ?, ?)", (prod, cant, unidad))
            conn.commit(); conn.close()
            self.cargar_stock()
            self.ent_stock_prod.delete(0, tk.END); self.ent_stock_cant.delete(0, tk.END)

    def cargar_stock(self):
        for i in self.tree_stock.get_children(): self.tree_stock.delete(i)
        
        # Configuramos los "tags" (etiquetas de color)
        self.tree_stock.tag_configure("critico", background="#e53935", foreground="white") # Rojo
        self.tree_stock.tag_configure("atencion", background="#ffb74d", foreground="black") # Naranja/Amarillo
        self.tree_stock.tag_configure("ok", foreground="white") # Normal

        conn = sqlite3.connect('verduleria_final.db')
        # Traemos también el ID para futuras operaciones
        for row in conn.execute("SELECT producto, cantidad, unidad FROM stock"):
            producto, cantidad, unidad = row
            
            # Lógica de semáforo (Podés ajustar los números 5 y 15 a tu gusto)
            tag = "ok"
            try:
                cant_num = float(cantidad)
                if cant_num <= 5: tag = "critico"     # Menos de 5 (kg/uni)
                elif cant_num <= 15: tag = "atencion" # Entre 5 y 15
            except:
                pass # Si la cantidad no es numero, lo deja en blanco

            self.tree_stock.insert("", tk.END, values=row, tags=(tag,))
        conn.close()

    # ==========================================
    # PESTAÑA 3: BALANCE Y ARQUEO
    # ==========================================
    def setup_balance(self):
        izq = ttk.Frame(self.frame_balance, padding=20)
        izq.pack(side="left", fill="both", expand=True)
        
        ttk.Label(izq, text="Resumen del Día (Arqueo)", font=("Arial", 16, "bold")).pack(pady=10)
        
        # También actualizamos los colores aquí para que se lean bien
        self.lbl_efectivo = ttk.Label(izq, text="Efectivo: $0", font=("Arial", 14), foreground="#00e676") # Verde Brillante
        self.lbl_efectivo.pack(anchor="w", pady=5)
        
        self.lbl_mp = ttk.Label(izq, text="Mercado Pago: $0", font=("Arial", 14), foreground="#40c4ff") # Azul claro
        self.lbl_mp.pack(anchor="w", pady=5)
        
        self.lbl_otros = ttk.Label(izq, text="Otros: $0", font=("Arial", 14))
        self.lbl_otros.pack(anchor="w", pady=5)
        
        ttk.Separator(izq).pack(fill="x", pady=15)
        
        self.lbl_gastos_total = ttk.Label(izq, text="Total Gastos: -$0", font=("Arial", 14), foreground="#ff8a80") # Rojo claro
        self.lbl_gastos_total.pack(anchor="w", pady=5)
        
        ttk.Separator(izq).pack(fill="x", pady=15)
        
        self.lbl_neto = ttk.Label(izq, text="GANANCIA REAL: $0", font=("Arial", 18, "bold"), bootstyle="inverse-primary")
        self.lbl_neto.pack(fill="x", pady=10)
        
        ttk.Button(izq, text="🔄 Recalcular Todo", command=self.actualizar_graficos).pack(pady=10)
        ttk.Button(izq, text="📄 Exportar para AFIP (Excel)", bootstyle="warning", command=self.exportar_afip).pack(pady=10)

        der = ttk.Frame(self.frame_balance, padding=10)
        der.pack(side="right", fill="both", expand=True)
        
        self.fig = Figure(figsize=(5, 4), dpi=90)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=der)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.actualizar_graficos()

    def actualizar_graficos(self):
        hoy = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect('verduleria_final.db')
        
        efectivo = 0; mp = 0; otros = 0
        rows = conn.execute("SELECT medio_pago, monto FROM ventas WHERE fecha LIKE ?", (f'{hoy}%',)).fetchall()
        for medio, monto in rows:
            if "Efectivo" in medio: efectivo += monto
            elif "Mercado" in medio: mp += monto
            else: otros += monto
            
        gastos = conn.execute("SELECT SUM(monto) FROM gastos WHERE fecha LIKE ?", (f'{hoy}%',)).fetchone()[0] or 0
        conn.close()
        
        self.lbl_efectivo.config(text=f"💵 Efectivo (Billetes): ${efectivo:,.0f}")
        self.lbl_mp.config(text=f"📱 Mercado Pago: ${mp:,.0f}")
        self.lbl_otros.config(text=f"💳 Otros: ${otros:,.0f}")
        self.lbl_gastos_total.config(text=f"🛑 Gastos del día: -${gastos:,.0f}")
        
        neto = (efectivo + mp + otros) - gastos
        self.lbl_neto.config(text=f" GANANCIA HOY: ${neto:,.0f} ")

        self.ax.clear()
        categorias = ['Efectivo', 'MP/Digital', 'Gastos']
        valores = [efectivo, mp + otros, gastos]
        # Colores para el gráfico también ajustados
        colores = ['#00e676', '#40c4ff', '#ff5252']
        
        self.ax.bar(categorias, valores, color=colores)
        self.ax.set_title(f"Balance Financiero {hoy}")
        self.canvas.draw()

    def exportar_afip(self):
        try:
            conn = sqlite3.connect('verduleria_final.db')
            # Traemos solo ventas con DNI cargado o todas, según prefiera el contador
            df = pd.read_sql_query("SELECT fecha, dni, monto FROM ventas", conn)
            conn.close()
            
            if df.empty:
                messagebox.showinfo("Aviso", "No hay ventas para exportar.")
                return

            # Generamos nombre con fecha actual
            filename = f"Ventas_AFIP_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            
            # Exportamos a Excel
            df.to_excel(filename, index=False)
            messagebox.showinfo("Éxito", f"Reporte guardado como: {filename}")
            
            # Opcional: Abrir el archivo automáticamente
            os.startfile(filename) 
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def validar_solo_numeros(self, texto_nuevo):
        # Esta función devuelve True si el texto es válido, False si no.
        # %P es el texto "propuesto" (cómo quedaría si aceptamos el cambio)
        
        if texto_nuevo == "": 
            return True  # Permitir borrar todo y dejar vacío
        if texto_nuevo.isdigit():
            # Opcional: Podés limitar el largo a 8 caracteres (típico DNI)
            if len(texto_nuevo) <= 8: 
                return True
            else:
                return False # Rechazar si pasa de 8 dígitos
        return False # Rechazar si tiene letras o símbolos
    
    def generar_ticket_texto(self, monto, dni, medio):
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        ticket = f"""
        ********************************
             LA VERDULERÍA DEL BARRIO
        ********************************
        Fecha: {fecha}
        --------------------------------
        Cliente DNI: {dni if dni else "Consumidor Final"}
        Medio Pago: {medio}
        --------------------------------
        TOTAL A PAGAR:    ${monto:,.2f}
        --------------------------------
        
        ¡Gracias por su compra!
        IG: @TuVerduleria
        ********************************
        """
        # Acá podrías mandarlo a imprimir, por ahora lo mostramos
        messagebox.showinfo("Ticket de Venta", ticket)

    # ==========================================
    # PESTAÑA 4: REPORTES Y PDF
    # ==========================================
    def setup_reportes(self):
        panel = ttk.Frame(self.frame_reportes, padding=20)
        panel.pack(fill="both", expand=True)

        # --- FILTROS DE FECHA ---
        filtros = ttk.Labelframe(panel, text=" Rango de Fechas ", padding=15)
        filtros.pack(fill="x", pady=10)
        
        ttk.Label(filtros, text="Desde:").pack(side="left", padx=5)
        self.date_desde = ttk.DateEntry(filtros, bootstyle="primary", firstweekday=0, dateformat="%Y-%m-%d")
        self.date_desde.pack(side="left", padx=5)
        
        ttk.Label(filtros, text="Hasta:").pack(side="left", padx=5)
        self.date_hasta = ttk.DateEntry(filtros, bootstyle="primary", firstweekday=0, dateformat="%Y-%m-%d")
        self.date_hasta.pack(side="left", padx=5)
        
        ttk.Button(filtros, text="🔍 Buscar Ventas", bootstyle="info", command=self.filtrar_ventas).pack(side="left", padx=20)
        ttk.Button(filtros, text="📄 Generar PDF", bootstyle="danger", command=self.generar_pdf_reporte).pack(side="left", padx=5)

        # --- TABLA DE RESULTADOS ---
        self.tree_rep = ttk.Treeview(panel, columns=("Fecha", "DNI", "Pago", "Monto"), show="headings", bootstyle="secondary")
        self.tree_rep.heading("Fecha", text="Fecha"); self.tree_rep.column("Fecha", width=150)
        self.tree_rep.heading("DNI", text="Cliente / DNI"); self.tree_rep.column("DNI", width=150)
        self.tree_rep.heading("Pago", text="Medio Pago"); self.tree_rep.column("Pago", width=150)
        self.tree_rep.heading("Monto", text="Monto"); self.tree_rep.column("Monto", width=100)
        self.tree_rep.pack(fill="both", expand=True, pady=10)

        # --- LABEL DE TOTAL ---
        self.lbl_total_reporte = ttk.Label(panel, text="Total Ventas en Período: $0", font=("Arial", 16, "bold"), bootstyle="inverse-success")
        self.lbl_total_reporte.pack(fill="x", pady=10)

    def filtrar_ventas(self):
        # Obtenemos las fechas del widget DateEntry
        f_desde = self.date_desde.entry.get()
        f_hasta = self.date_hasta.entry.get()
        
        conn = sqlite3.connect('verduleria_final.db')
        # Hacemos la query entre fechas (agregamos hora 00:00 y 23:59 para cubrir todo el día)
        query = "SELECT fecha, dni, medio_pago, monto FROM ventas WHERE fecha BETWEEN ? AND ?"
        rows = conn.execute(query, (f"{f_desde} 00:00:00", f"{f_hasta} 23:59:59")).fetchall()
        conn.close()

        # Limpiar tabla
        for i in self.tree_rep.get_children(): self.tree_rep.delete(i)
        
        total = 0
        for row in rows:
            self.tree_rep.insert("", tk.END, values=(row[0], row[1], row[2], f"${row[3]:,.2f}"))
            total += row[3]
            
        self.lbl_total_reporte.config(text=f"Total Ventas en Período: ${total:,.2f}")
        return rows, total # Devolvemos los datos por si los usa el PDF

    def generar_pdf_reporte(self):
        # Primero ejecutamos el filtro para tener los datos frescos
        datos, total = self.filtrar_ventas()
        
        if not datos:
            messagebox.showwarning("Vacío", "No hay ventas en ese rango para generar el reporte.")
            return

        f_desde = self.date_desde.entry.get()
        f_hasta = self.date_hasta.entry.get()
        filename = f"Reporte_Ventas_{f_desde}_a_{f_hasta}.pdf"

        try:
            doc = SimpleDocTemplate(filename, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            # 1. LOGO Y ENCABEZADO
            # Intentamos cargar logo.png si existe
            try:
                logo = Image('./icons/logo.png', width=150, height=100) 
                logo.hAlign = 'CENTER'
                elements.append(logo)
            except:
                pass # Si no hay logo, no pasa nada

            # Título Empresa
            elements.append(Paragraph("<b>VERDULERÍA EL BARRIO</b>", styles['Title']))
            elements.append(Paragraph(f"Reporte de Ventas: {f_desde} al {f_hasta}", styles['Normal']))
            elements.append(Spacer(1, 20))

            # 2. TABLA DE DATOS
            # Encabezados de tabla
            data_tabla = [["FECHA", "CLIENTE/DNI", "MEDIO PAGO", "MONTO"]]
            
            # Cuerpo de tabla
            for row in datos:
                data_tabla.append([row[0], row[1], row[2], f"${row[3]:,.2f}"])
            
            # Fila de TOTAL
            data_tabla.append(["", "", "TOTAL PERÍODO:", f"${total:,.2f}"])

            # Estilo de la tabla
            t = Table(data_tabla)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey), # Encabezado Gris
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), # Texto Blanco en encabezado
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige), # Filas color crema
                ('GRID', (0, 0), (-1, -1), 1, colors.black), # Bordes negros
                ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'), # Total en Negrita
                ('BACKGROUND', (-2, -1), (-1, -1), colors.lightgrey), # Fondo del total
            ]))
            
            elements.append(t)
            
            # Pie de página simple
            elements.append(Spacer(1, 40))
            elements.append(Paragraph("Generado por Sistema VerduSoft", styles['Italic']))

            # 3. GENERAR
            doc.build(elements)
            messagebox.showinfo("Éxito", f"PDF Generado correctamente:\n{filename}")
            os.startfile(filename) # Abrir automáticamente

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el PDF: {e}")

    def verificar_datos_prueba(self):
        # Conectamos para ver cuántas ventas hay
        conn = sqlite3.connect('verduleria_final.db')
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ventas")
            cantidad_ventas = cursor.fetchone()[0]
            
            # SI LA BASE ESTÁ VACÍA (0 ventas), preguntamos si quiere cargar
            if cantidad_ventas == 0:
                respuesta = messagebox.askyesno("Modo Prueba", 
                    "La base de datos está vacía.\n¿Querés cargar datos de prueba automáticos?")
                
                if respuesta:
                    # Llamamos a la función del OTRO archivo
                    cargar_datos_prueba.poblar_db()
                    
                    # Refrescamos todas las pantallas para que se vean los datos ya
                    self.cargar_movimientos()
                    self.actualizar_graficos()
                    self.cargar_stock()
                    messagebox.showinfo("Listo", "¡Datos de prueba cargados!")
        except Exception as e:
            print(f"Error verificando datos: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    app = ttk.Window(themename="superhero")
    VerduleriaFinal(app)
    app.mainloop()