import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import os
import sqlite3
from datetime import datetime

# Imports para PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Imports para Gráficos
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Importar conexión
import database

class ReportesView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(fill="both", expand=True)
        self.setup_ui()

    def setup_ui(self):
        panel = ttk.Frame(self, padding=20)
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
        ttk.Button(filtros, text="📈 Ver Gráficos", bootstyle="success", command=self.mostrar_dashboard).pack(side="left", padx=5)

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
        f_desde = self.date_desde.entry.get()
        f_hasta = self.date_hasta.entry.get()
        
        conn = database.get_connection()
        
        # CAMBIO CLAVE AQUÍ:
        # Agregamos "AND medio_pago != 'Pago Deuda'"
        # Esto hace que la base de datos ignore completamente los cobros de deudas en este listado.
        query = """
            SELECT fecha, dni, medio_pago, monto 
            FROM ventas 
            WHERE fecha BETWEEN ? AND ? 
            AND medio_pago != 'Pago Deuda'
        """
        
        rows = conn.execute(query, (f"{f_desde} 00:00:00", f"{f_hasta} 23:59:59")).fetchall()
        conn.close()

        # Limpiar tabla visual
        for i in self.tree_rep.get_children(): self.tree_rep.delete(i)
        
        total = 0
        for row in rows:
            # Ahora mostramos todo lo que traiga la consulta, porque ya filtramos los pagos antes
            self.tree_rep.insert("", tk.END, values=(row[0], row[1], row[2], f"${row[3]:,.2f}"))
            total += row[3]
            
        self.lbl_total_reporte.config(text=f"Total Ventas (Mercadería Real): ${total:,.2f}")
        return rows, total

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

            # 1. LOGO Y ENCABEZADO (Recuperado)
            try:
                # Buscamos logo en la carpeta raíz (un nivel arriba) o en la misma carpeta
                if os.path.exists("logo.png"): logo_path = "logo.png"
                elif os.path.exists("../logo.png"): logo_path = "../logo.png"
                else: logo_path = None

                if logo_path:
                    logo = Image(logo_path, width=50, height=50) 
                    logo.hAlign = 'LEFT'
                    elements.append(logo)
            except:
                pass 

            # Título Empresa
            elements.append(Paragraph("<b>VERDULERÍA EL BARRIO</b>", styles['Title']))
            elements.append(Paragraph(f"Reporte de Ventas: {f_desde} al {f_hasta}", styles['Normal']))
            elements.append(Spacer(1, 20))

            # 2. TABLA DE DATOS (Estilo Recuperado)
            data_tabla = [["FECHA", "CLIENTE/DNI", "MEDIO PAGO", "MONTO"]]
            for row in datos:
                data_tabla.append([row[0], row[1], row[2], f"${row[3]:,.2f}"])
            
            data_tabla.append(["", "", "TOTAL PERÍODO:", f"${total:,.2f}"])

            t = Table(data_tabla)
            # Estilo detallado que tenías antes
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey), # Encabezado Gris
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), 
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige), # Filas color crema
                ('GRID', (0, 0), (-1, -1), 1, colors.black), 
                ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'), # Total en Negrita
                ('BACKGROUND', (-2, -1), (-1, -1), colors.lightgrey), 
            ]))
            
            elements.append(t)
            
            elements.append(Spacer(1, 40))
            elements.append(Paragraph("Generado por Sistema VerduSoft", styles['Italic']))

            doc.build(elements)
            messagebox.showinfo("Éxito", f"PDF Generado correctamente:\n{filename}")
            os.startfile(filename) 

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el PDF: {e}")

    def mostrar_dashboard(self):
        conn = database.get_connection()
        df = pd.read_sql_query("SELECT fecha, dni, monto FROM ventas", conn)
        conn.close()

        if df.empty:
            messagebox.showinfo("Sin datos", "No hay ventas suficientes.")
            return

        # Procesamiento de Fechas
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['hora'] = df['fecha'].dt.hour
        df['fecha_solo'] = df['fecha'].dt.date # Necesario para el 3er gráfico

        # --- VENTANA POPUP ---
        top = tk.Toplevel(self)
        top.title("Dashboard Gerencial - VerduSoft")
        top.geometry("1200x600")
        
        frame_graficos = ttk.Frame(top)
        frame_graficos.pack(fill="both", expand=True, padx=10, pady=10)

        fig = Figure(figsize=(10, 5), dpi=100)
        
        # --- GRÁFICO 1: HORARIOS PICO ---
        ventas_por_hora = df.groupby('hora').size()
        ax1 = fig.add_subplot(131) # 1 fila, 3 columnas (Posición 1)
        horas_completas = range(8, 22)
        ventas_reindex = ventas_por_hora.reindex(horas_completas, fill_value=0)
        
        ax1.bar(ventas_reindex.index, ventas_reindex.values, color='#ffb74d')
        ax1.set_title("Horarios Pico")
        ax1.set_xlabel("Hora")
        ax1.grid(axis='y', linestyle='--', alpha=0.7)

        # --- GRÁFICO 2: TOP 5 CLIENTES ---
        top_clientes = df.groupby('dni')['monto'].sum().sort_values(ascending=False).head(5)
        ax2 = fig.add_subplot(132) # Posición 2
        top_clientes = top_clientes.sort_values(ascending=True) 
        
        ax2.barh(top_clientes.index.astype(str), top_clientes.values, color='#66bb6a')
        ax2.set_title("Top 5 Clientes ($)")

        # --- GRÁFICO 3: TICKET PROMEDIO (RECUPERADO) ---
        ticket_promedio = df.groupby('fecha_solo')['monto'].mean().tail(15)
        
        ax3 = fig.add_subplot(133) # Posición 3
        fechas_str = [d.strftime("%d/%m") for d in ticket_promedio.index]
        
        ax3.plot(fechas_str, ticket_promedio.values, marker='o', color='#29b6f6', linewidth=2)
        ax3.set_title("Ticket Promedio (Últimos 15 días)")
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, linestyle='--', alpha=0.5)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)