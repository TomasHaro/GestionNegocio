import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import pandas as pd
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import database

class BalanceView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(fill="both", expand=True)
        self.setup_ui()

    def setup_ui(self):
        izq = ttk.Frame(self, padding=20)
        izq.pack(side="left", fill="both", expand=True)
        
        ttk.Label(izq, text="Resumen del Día (Arqueo)", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.lbl_efectivo = ttk.Label(izq, text="Efectivo: $0", font=("Arial", 14), foreground="#00e676")
        self.lbl_efectivo.pack(anchor="w", pady=5)
        
        self.lbl_mp = ttk.Label(izq, text="Mercado Pago: $0", font=("Arial", 14), foreground="#40c4ff")
        self.lbl_mp.pack(anchor="w", pady=5)
        
        self.lbl_otros = ttk.Label(izq, text="Otros: $0", font=("Arial", 14))
        self.lbl_otros.pack(anchor="w", pady=5)
        
        ttk.Separator(izq).pack(fill="x", pady=15)
        
        self.lbl_gastos_total = ttk.Label(izq, text="Total Gastos: -$0", font=("Arial", 14), foreground="#ff8a80")
        self.lbl_gastos_total.pack(anchor="w", pady=5)
        
        ttk.Separator(izq).pack(fill="x", pady=15)
        
        self.lbl_neto = ttk.Label(izq, text="GANANCIA REAL: $0", font=("Arial", 18, "bold"), bootstyle="inverse-primary")
        self.lbl_neto.pack(fill="x", pady=10)
        
        ttk.Button(izq, text="🔄 Recalcular Todo", command=self.actualizar_graficos).pack(pady=10)
        ttk.Button(izq, text="📄 Exportar para AFIP", bootstyle="warning", command=self.exportar_afip).pack(pady=10)

        der = ttk.Frame(self, padding=10)
        der.pack(side="right", fill="both", expand=True)
        
        self.fig = Figure(figsize=(5, 4), dpi=90)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=der)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.actualizar_graficos()

    def actualizar_graficos(self):
        hoy = datetime.now().strftime("%Y-%m-%d")
        conn = database.get_connection()
        
        # 1. Inicializamos contadores en 0
        efectivo_caja = 0      # Plata física (Billetes en el cajón)
        mp_caja = 0            # Plata digital (Mercado Pago / Bancos)
        fiado_calle = 0        # Plata que te deben (Cuenta Corriente)
        
        # 2. Traemos las ventas del día
        rows = conn.execute("SELECT medio_pago, monto FROM ventas WHERE fecha LIKE ?", (f'{hoy}%',)).fetchall()
        
        for medio, monto in rows:
            if medio == "Efectivo":
                efectivo_caja += monto
            elif medio == "Pago Deuda": 
                # Cuando te pagan una deuda vieja, entra PLATA al cajón
                efectivo_caja += monto 
            elif "Mercado" in medio or "Debito" in medio or "Credito" in medio:
                mp_caja += monto
            elif medio == "Cuenta Corriente":
                fiado_calle += monto # Esto es venta, pero NO es plata
            
        # 3. Traemos los gastos
        gastos = conn.execute("SELECT SUM(monto) FROM gastos WHERE fecha LIKE ?", (f'{hoy}%',)).fetchone()[0] or 0
        conn.close()
        
        # --- ACTUALIZAR TEXTOS (LABELS) ---
        self.lbl_efectivo.config(text=f"💵 Efectivo en Cajón: ${efectivo_caja:,.0f}")
        self.lbl_mp.config(text=f"📱 Digital (MP/Bco): ${mp_caja:,.0f}")
        self.lbl_otros.config(text=f"📒 Fiado (A cobrar): ${fiado_calle:,.0f}")
        self.lbl_gastos_total.config(text=f"🛑 Gastos: -${gastos:,.0f}")
        
        # Caja Real = Lo que tenés disponible para usar hoy (Efectivo + Banco - Gastos)
        # (Lo fiado no se cuenta porque no podés pagar la luz con fiados)
        caja_real = (efectivo_caja + mp_caja) - gastos
        self.lbl_neto.config(text=f" CAJA REAL HOY: ${caja_real:,.0f} ")

        # --- GRÁFICO DE 4 BARRAS ---
        self.ax.clear()
        
        # Definimos las 4 Categorías
        categorias = ['Efectivo', 'Digital', 'Fiado', 'Gastos']
        valores = [efectivo_caja, mp_caja, fiado_calle, gastos]
        
        # Colores para diferenciar bien:
        # Verde (Efectivo), Azul (Digital), Naranja (Fiado/Alerta), Rojo (Gastos)
        colores = ['#00e676', '#2979ff', '#ffb74d', '#ff5252'] 
        
        barras = self.ax.bar(categorias, valores, color=colores)
        
        # Agregamos el monto exacto arriba de cada barrita para leer rápido
        for bar in barras:
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width()/2., height,
                         f'${int(height)}',
                         ha='center', va='bottom', fontsize=9, fontweight='bold')

        self.ax.set_title(f"Balance Detallado {hoy}")
        
        # Ajustamos un poco los márgenes para que entren los números
        self.fig.tight_layout()
        self.canvas.draw()

    def exportar_afip(self):
        try:
            conn = database.get_connection()
            df = pd.read_sql_query("SELECT fecha, dni, monto FROM ventas", conn)
            conn.close()
            if df.empty:
                messagebox.showinfo("Aviso", "No hay ventas.")
                return
            filename = f"Ventas_AFIP_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            df.to_excel(filename, index=False)
            messagebox.showinfo("Éxito", f"Guardado: {filename}")
            os.startfile(filename) 
        except Exception as e:
            messagebox.showerror("Error", str(e))