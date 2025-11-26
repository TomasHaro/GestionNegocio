import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import database # Importamos nuestro modulo de DB

class CajaView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller # Referencia a la app principal
        self.pack(fill="both", expand=True)
        self.setup_ui()
        
    def setup_ui(self):
        # --- LADO IZQUIERDO: COBRO ---
        izq = ttk.Labelframe(self, text=" Nueva Venta ", padding=20, bootstyle="info", width=400)
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
        self.combo_pago = ttk.Combobox(izq, values=["Efectivo", "Mercado Pago", "Débito", "Crédito", "Cuenta Corriente"], state="readonly", font=("Arial", 12))
        self.combo_pago.current(0)
        self.combo_pago.pack(fill="x", pady=(5, 15))

        # 3. DNI
        ttk.Label(izq, text="DNI Cliente (OBLIGATORIO):", bootstyle="danger").pack(anchor="w")
        
        vcmd = (self.register(self.validar_solo_numeros), '%P')
        self.entry_dni = ttk.Entry(izq, font=("Arial", 12), validate="key", validatecommand=vcmd)
        self.entry_dni.pack(fill="x", pady=(5, 20))

        # Botones
        btn_cobrar = ttk.Button(izq, text="CONFIRMAR VENTA (Enter)", bootstyle="success", command=self.registrar_venta)
        btn_cobrar.pack(fill="x", ipady=10)
        ttk.Separator(izq, orient='horizontal').pack(fill='x', pady=20)
        ttk.Button(izq, text="🛑 REGISTRAR GASTO", bootstyle="danger", command=self.registrar_gasto).pack(fill="x")

        # --- LADO DERECHO: LISTA ---
        der = ttk.Frame(self, padding=10)
        der.pack(side="right", fill="both", expand=True)
        
        ttk.Label(der, text="Últimos Movimientos", font=("Arial", 12, "bold")).pack(anchor="w")
        
        cols = ("Hora", "Tipo", "Detalle/DNI", "Monto")
        self.tree_mov = ttk.Treeview(der, columns=cols, show="headings", bootstyle="primary")
        self.tree_mov.heading("Hora", text="Hora"); self.tree_mov.column("Hora", width=80)
        self.tree_mov.heading("Tipo", text="Tipo"); self.tree_mov.column("Tipo", width=80)
        self.tree_mov.heading("Detalle/DNI", text="Detalle / DNI"); self.tree_mov.column("Detalle/DNI", width=150)
        self.tree_mov.heading("Monto", text="Monto"); self.tree_mov.column("Monto", width=100)
        self.tree_mov.pack(fill="both", expand=True)
        
        self.tree_mov.tag_configure("g", foreground="#ff8a80")
        self.tree_mov.tag_configure("v", foreground="#00e676")
        
        self.cargar_movimientos()

    def registrar_venta(self):
        dni = self.entry_dni.get().strip()
        if not dni:
            messagebox.showwarning("Falta DNI", "🛑 El campo DNI es OBLIGATORIO.")
            self.entry_dni.focus()
            return
        if len(dni) < 7:
             messagebox.showwarning("Error", "El DNI parece incompleto.")
             self.entry_dni.focus()
             return
        try:
            monto = float(self.entry_monto.get())
            if monto <= 0: raise ValueError
        except:
            messagebox.showerror("Error", "Ingresa un monto válido.")
            return

        medio = self.combo_pago.get()
        conn = database.get_connection()
        
        if medio == "Cuenta Corriente":
            # LOGICA DE FIADO
            # 1. Verificamos si el cliente tiene cuenta
            cursor = conn.cursor()
            cursor.execute("SELECT saldo FROM clientes WHERE dni = ?", (dni,))
            cliente = cursor.fetchone()
            
            if not cliente:
                # Si no tiene cuenta, preguntamos si creamos
                if messagebox.askyesno("Atención", "Este DNI no tiene cuenta corriente.\n¿Crear cuenta y anotar deuda?"):
                    conn.execute("INSERT INTO clientes (dni, nombre, saldo) VALUES (?, 'Cliente', ?)", (dni, monto))
                else:
                    conn.close()
                    return # Cancelar venta
            else:
                # Si ya existe, sumamos la deuda
                nuevo_saldo = cliente[0] + monto
                conn.execute("UPDATE clientes SET saldo = ? WHERE dni = ?", (nuevo_saldo, dni))
            
            # Registramos la venta igual, pero en el reporte saldrá medio_pago='Cuenta Corriente'
            # (Ojo: Esto suma al reporte de ventas pero NO suma plata a la caja del día en Efectivo)
            conn.execute("INSERT INTO ventas (fecha, dni, medio_pago, monto) VALUES (?, ?, ?, ?)",
                     (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), dni, medio, monto))
            
            messagebox.showinfo("Anotado", f"Se agregaron ${monto:,.2f} a la deuda del cliente.")

        else:
            # VENTA NORMAL
            conn.execute("INSERT INTO ventas (fecha, dni, medio_pago, monto) VALUES (?, ?, ?, ?)",
                     (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), dni, medio, monto))
        conn.commit(); conn.close()
        
        self.generar_ticket_texto(monto, dni, self.combo_pago.get())
        self.entry_monto.delete(0, tk.END); self.entry_dni.delete(0, tk.END)
        self.entry_monto.focus()
        
        # ACTUALIZAR TODO EL SISTEMA
        self.controller.refresh_all()

    def registrar_gasto(self):
        desc = simpledialog.askstring("Gasto", "Descripción:", parent=self)
        if desc:
            self.update() 
            monto = simpledialog.askfloat("Gasto", "Monto ($):", parent=self)
            if monto:
                conn = database.get_connection()
                conn.execute("INSERT INTO gastos (fecha, descripcion, monto) VALUES (?, ?, ?)", 
                             (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), desc, monto))
                conn.commit(); conn.close()
                self.controller.refresh_all()

    def cargar_movimientos(self):
        for i in self.tree_mov.get_children(): self.tree_mov.delete(i)
        conn = database.get_connection()
        hoy = datetime.now().strftime("%Y-%m-%d")
        
        ventas = [("VENTA", r[0], r[1] if r[1] else "Consumidor Final", r[2]) for r in conn.execute("SELECT fecha, dni, monto FROM ventas WHERE fecha LIKE ?", (f'{hoy}%',))]
        gastos = [("GASTO", r[0], r[1], r[2] * -1) for r in conn.execute("SELECT fecha, descripcion, monto FROM gastos WHERE fecha LIKE ?", (f'{hoy}%',))]
        
        todos = sorted(ventas + gastos, key=lambda x: x[1], reverse=True)
        for tipo, fecha, det, monto in todos:
            hora = fecha.split(" ")[1][:5]
            tag = "g" if tipo == "GASTO" else "v"
            self.tree_mov.insert("", tk.END, values=(hora, tipo, det, f"${monto:,.2f}"), tags=(tag,))
        conn.close()

    def validar_solo_numeros(self, texto_nuevo):
        if texto_nuevo == "": return True
        if texto_nuevo.isdigit() and len(texto_nuevo) <= 8: return True
        return False
    
    def generar_ticket_texto(self, monto, dni, medio):
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        ticket = f"""
        ********************************
             LA VERDULERÍA DEL BARRIO
        ********************************
        Fecha: {fecha}
        Cliente DNI: {dni}
        Medio: {medio}
        TOTAL: ${monto:,.2f}
        ********************************
        """
        messagebox.showinfo("Ticket de Venta", ticket)