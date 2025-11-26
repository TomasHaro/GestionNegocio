import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import database

class FiadosView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(fill="both", expand=True)
        self.setup_ui()

    def setup_ui(self):
        # --- PANEL SUPERIOR: BUSCAR CLIENTE ---
        panel_top = ttk.Labelframe(self, text=" Buscar Cliente (Deudor) ", padding=15, bootstyle="warning")
        panel_top.pack(fill="x", padx=10, pady=10)

        ttk.Label(panel_top, text="DNI Cliente:").pack(side="left", padx=5)
        self.entry_dni = ttk.Entry(panel_top, font=("Arial", 12), width=15)
        self.entry_dni.pack(side="left", padx=5)
        
        ttk.Button(panel_top, text="🔍 Buscar Estado", bootstyle="warning", command=self.buscar_cliente).pack(side="left", padx=10)

        # --- PANEL CENTRAL: RESULTADO ---
        self.frame_resultado = ttk.Frame(self, padding=20)
        self.frame_resultado.pack(fill="both", expand=True)
        
        # Labels gigantes para mostrar la deuda
        self.lbl_nombre = ttk.Label(self.frame_resultado, text="Cliente: -", font=("Arial", 14))
        self.lbl_nombre.pack(pady=5)
        
        self.lbl_deuda = ttk.Label(self.frame_resultado, text="DEUDA ACTUAL: $0", font=("Arial", 24, "bold"), foreground="#ff5252")
        self.lbl_deuda.pack(pady=10)

        # Botón para pagar deuda
        self.btn_pagar = ttk.Button(self.frame_resultado, text="💸 REGISTRAR PAGO DE DEUDA", bootstyle="success", state="disabled", command=self.pagar_deuda)
        self.btn_pagar.pack(pady=10, ipady=10, fill="x")
        
        # Historial simple
        ttk.Label(self.frame_resultado, text="Nota: Los detalles de cada compra se ven en Reportes filtrando por DNI.").pack(side="bottom", pady=20)

    def buscar_cliente(self):
        dni = self.entry_dni.get().strip()
        if not dni: return

        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Buscamos si existe en la tabla clientes
        cursor.execute("SELECT nombre, saldo FROM clientes WHERE dni = ?", (dni,))
        data = cursor.fetchone()
        
        if data:
            nombre, saldo = data
            self.lbl_nombre.config(text=f"Cliente DNI: {dni} ({nombre})")
            self.lbl_deuda.config(text=f"DEUDA ACTUAL: ${saldo:,.2f}")
            self.btn_pagar.config(state="normal")
            self.current_dni = dni
            self.current_saldo = saldo
        else:
            # Si no existe, preguntamos si queremos crearlo
            if messagebox.askyesno("Nuevo", "El cliente no tiene cuenta corriente abierta.\n¿Abrir cuenta nueva?"):
                nombre = simpledialog.askstring("Nombre", "Nombre del Cliente (para recordar):")
                if nombre:
                    conn.execute("INSERT INTO clientes (dni, nombre, saldo) VALUES (?, ?, 0)", (dni, nombre))
                    conn.commit()
                    self.buscar_cliente() # Recargamos
        conn.close()

    def pagar_deuda(self):
        # Registrar que el cliente pagó parte o toda su deuda
        monto = simpledialog.askfloat("Saldar Deuda", f"El cliente debe ${self.current_saldo:,.2f}.\n¿Cuánto paga hoy?")
        
        if monto and monto > 0:
            if monto > self.current_saldo:
                messagebox.showwarning("Error", "No puede pagar más de lo que debe.")
                return

            conn = database.get_connection()
            # 1. Descontamos saldo
            nuevo_saldo = self.current_saldo - monto
            conn.execute("UPDATE clientes SET saldo = ? WHERE dni = ?", (nuevo_saldo, self.current_dni))
            
            # 2. Registramos el ingreso de dinero en CAJA (como una venta especial o ingreso)
            # Lo registramos como venta para que cuadre la caja del día, pero con detalle "PAGO DEUDA"
            conn.execute("INSERT INTO ventas (fecha, dni, medio_pago, monto) VALUES (?, ?, ?, ?)",
                         (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_dni, "Pago Deuda", monto))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito", "Pago registrado y caja actualizada.")
            self.buscar_cliente() # Refrescar pantalla
            self.controller.refresh_all() # Actualizar caja