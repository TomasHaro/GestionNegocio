import ttkbootstrap as ttk
import tkinter as tk
import database

class StockView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(fill="both", expand=True)
        self.setup_ui()

    def setup_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        
        ttk.Label(top, text="Producto:").pack(side="left")
        self.ent_stock_prod = ttk.Entry(top, width=20); self.ent_stock_prod.pack(side="left", padx=5)
        
        ttk.Label(top, text="Cantidad:").pack(side="left")
        self.ent_stock_cant = ttk.Entry(top, width=10); self.ent_stock_cant.pack(side="left", padx=5)

        ttk.Label(top, text="Unidad:").pack(side="left")
        self.combo_unidad = ttk.Combobox(top, values=["Kg", "Unidad", "Bolsa", "Cajón"], width=10); self.combo_unidad.current(0)
        self.combo_unidad.pack(side="left", padx=5)
        
        ttk.Button(top, text="Guardar", command=self.guardar_stock).pack(side="left", padx=10)

        self.tree_stock = ttk.Treeview(self, columns=("Producto", "Cantidad", "Unidad"), show="headings", bootstyle="primary")
        self.tree_stock.heading("Producto", text="Producto"); self.tree_stock.heading("Cantidad", text="Cantidad Actual"); self.tree_stock.heading("Unidad", text="Unidad")
        self.tree_stock.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree_stock.tag_configure("critico", background="#e53935", foreground="white")
        self.tree_stock.tag_configure("atencion", background="#ffb74d", foreground="black")
        self.tree_stock.tag_configure("ok", foreground="white")
        
        self.cargar_stock()

    def guardar_stock(self):
        prod = self.ent_stock_prod.get()
        cant = self.ent_stock_cant.get()
        unidad = self.combo_unidad.get()
        
        if prod and cant:
            conn = database.get_connection()
            cursor = conn.execute("SELECT id FROM stock WHERE producto = ?", (prod,))
            data = cursor.fetchone()
            if data: conn.execute("UPDATE stock SET cantidad = ?, unidad = ? WHERE id = ?", (cant, unidad, data[0]))
            else: conn.execute("INSERT INTO stock (producto, cantidad, unidad) VALUES (?, ?, ?)", (prod, cant, unidad))
            conn.commit(); conn.close()
            self.cargar_stock()
            self.ent_stock_prod.delete(0, tk.END); self.ent_stock_cant.delete(0, tk.END)

    def cargar_stock(self):
        for i in self.tree_stock.get_children(): self.tree_stock.delete(i)
        conn = database.get_connection()
        for row in conn.execute("SELECT producto, cantidad, unidad FROM stock"):
            cantidad = row[1]
            tag = "ok"
            try:
                cant_num = float(cantidad)
                if cant_num <= 5: tag = "critico"
                elif cant_num <= 15: tag = "atencion"
            except: pass
            self.tree_stock.insert("", tk.END, values=row, tags=(tag,))
        conn.close()