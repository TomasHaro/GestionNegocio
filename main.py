import ttkbootstrap as ttk
import tkinter as tk
from tkinter import messagebox
import sqlite3
import database
import cargar_datos_prueba
# Importamos las vistas desde la carpeta views
from views.caja import CajaView
from views.fiados import FiadosView
from views.stock import StockView
from views.balance import BalanceView
from views.reportes import ReportesView

class VerduleriaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Verdulería - Sistema Profesional")
        self.root.geometry("1100x700") 
        
        # 1. Asegurar DB
        database.inicializar_db()
        
        # 2. Configurar Pestañas
        self.notebook = ttk.Notebook(self.root, bootstyle="primary")
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # 3. Inicializar Vistas
        # Les pasamos 'self' (controller) para que puedan llamar a refresh_all()
        self.view_caja = CajaView(self.notebook, controller=self)
        self.view_stock = StockView(self.notebook, controller=self)
        self.view_fiados = FiadosView(self.notebook, controller=self) # <--- NUEVA
        self.view_balance = BalanceView(self.notebook, controller=self)
        self.view_reportes = ReportesView(self.notebook, controller=self)

        self.notebook.add(self.view_caja, text="⚡ CAJA RÁPIDA")
        self.notebook.add(self.view_stock, text="📦 STOCK")
        self.notebook.add(self.view_fiados, text="📖 FIADOS") # <--- NUEVA PESTAÑA
        self.notebook.add(self.view_balance, text="💰 CIERRE")
        self.notebook.add(self.view_reportes, text="📊 REPORTES")

        # 4. Check de Datos de Prueba
        self.root.after(500, self.verificar_datos_prueba)

    def refresh_all(self):
        """Método central para actualizar todas las vistas cuando algo cambia"""
        self.view_caja.cargar_movimientos()
        self.view_balance.actualizar_graficos()
        # Stock y reportes no hace falta refrescarlos en tiempo real siempre, 
        # pero podríamos si quisieras:
        # self.view_stock.cargar_stock() 

    def verificar_datos_prueba(self):
        conn = database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ventas")
            if cursor.fetchone()[0] == 0:
                if messagebox.askyesno("Inicio", "¿Cargar datos de prueba?"):
                    cargar_datos_prueba.poblar_db()
                    self.refresh_all()
                    self.view_stock.cargar_stock()
        finally:
            conn.close()

if __name__ == "__main__":
    root = ttk.Window(themename="superhero")
    app = VerduleriaApp(root)
    root.mainloop()