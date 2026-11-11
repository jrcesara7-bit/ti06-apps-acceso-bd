"""HolaMundo02 en Python con interfaz de escritorio (Tkinter).

Pide usuario y contraseña de MySQL. Si la base acepta la conexión, muestra las asignaciones
de CPremier en una tabla con un buscador por trabajador.
Uso:  python holamundo02.py
"""
import tkinter as tk
from tkinter import ttk

import pymysql

import config

SQL = """
    SELECT t.nombre, t.oficio, e.dir_edificio, a.fecha_inicio, a.num_dias,
           a.num_dias * 8 * t.tarifa_hr AS monto
    FROM asignacion a
    JOIN trabajador t ON t.id_trabajador = a.id_trabajador
    JOIN edificio e ON e.id_edificio = a.id_edificio
    WHERE t.nombre LIKE %s
    ORDER BY a.fecha_inicio, t.nombre"""
COLUMNAS = [('Trabajador', 130, 'w'), ('Oficio', 110, 'w'), ('Edificio', 130, 'w'), ('Inicio', 90, 'w'),
            ('Días', 55, 'e'), ('Monto', 90, 'e')]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('HolaMundo02 · CPremier (Python + Tkinter + PyMySQL)')
        self.geometry('680x430')
        self.conexion = None
        self.protocol('WM_DELETE_WINDOW', self.salir)
        self.mostrar_login()

    # ------------------------------------------------------------ pantalla de acceso
    def mostrar_login(self):
        self.login = ttk.Frame(self, padding=30)
        self.login.pack(expand=True)
        ttk.Label(self.login, text='Acceso a CPremier', font=('', 14, 'bold')).grid(columnspan=2, pady=(0, 4))
        ttk.Label(self.login, text=f'Servidor {config.HOST}:{config.PUERTO} · base {config.BASE}').grid(
            columnspan=2, pady=(0, 14))
        ttk.Label(self.login, text='Usuario').grid(row=2, column=0, sticky='e', padx=6, pady=4)
        ttk.Label(self.login, text='Contraseña').grid(row=3, column=0, sticky='e', padx=6, pady=4)
        self.usuario = ttk.Entry(self.login, width=26)
        self.clave = ttk.Entry(self.login, width=26, show='•')   # la contraseña no se ve al escribir
        self.usuario.grid(row=2, column=1)
        self.clave.grid(row=3, column=1)
        self.aviso = ttk.Label(self.login, text='', foreground='#444444')
        self.aviso.grid(row=4, columnspan=2, pady=8)
        ttk.Button(self.login, text='Entrar', command=self.entrar).grid(row=5, columnspan=2)
        self.clave.bind('<Return>', lambda _evento: self.entrar())
        self.usuario.focus()

    def entrar(self):
        """Valida el acceso intentando abrir la conexión con lo que escribió la persona."""
        try:
            self.conexion = pymysql.connect(host=config.HOST, port=config.PUERTO, database=config.BASE,
                                            user=self.usuario.get(), password=self.clave.get())
        except pymysql.OperationalError as error:
            # 1045 es el código de MySQL para acceso denegado. Cualquier otro es problema de red o del servidor.
            self.aviso['text'] = ('Usuario o contraseña incorrectos.' if error.args[0] == 1045
                                  else 'No se pudo conectar con el servidor.')
            self.clave.delete(0, 'end')
            return
        nombre = self.usuario.get()
        self.login.destroy()   # la contraseña no se guarda, solo queda la conexión abierta
        self.mostrar_consulta(nombre)

    # ------------------------------------------------------------ pantalla de consulta
    def mostrar_consulta(self, nombre):
        barra = ttk.Frame(self, padding=(10, 10, 10, 4))
        barra.pack(fill='x')
        ttk.Label(barra, text='Buscar trabajador').pack(side='left')
        self.buscar = ttk.Entry(barra, width=22)
        self.buscar.pack(side='left', padx=6)
        self.buscar.bind('<Return>', lambda _evento: self.consultar())
        ttk.Button(barra, text='Consultar', command=self.consultar).pack(side='left')
        ttk.Label(barra, text=f'Sesión de {nombre}').pack(side='right')
        self.tabla = ttk.Treeview(self, columns=[c[0] for c in COLUMNAS], show='headings')
        for titulo, ancho, lado in COLUMNAS:
            self.tabla.heading(titulo, text=titulo)
            self.tabla.column(titulo, width=ancho, anchor=lado)
        self.tabla.pack(fill='both', expand=True, padx=10)
        self.estado = ttk.Label(self, padding=10)
        self.estado.pack(fill='x')
        self.consultar()

    def consultar(self):
        with self.conexion.cursor() as cursor:
            # Consulta parametrizada. El texto del buscador nunca se concatena al SQL.
            cursor.execute(SQL, (f'%{self.buscar.get().strip()}%',))
            filas = cursor.fetchall()
        self.tabla.delete(*self.tabla.get_children())
        for nombre, oficio, edificio, inicio, dias, monto in filas:
            self.tabla.insert('', 'end', values=(nombre, oficio, edificio, inicio, dias, f'{monto:,.2f}'))
        total = sum(f[5] for f in filas)
        self.estado['text'] = f'{len(filas)} registro(s) · monto total {total:,.2f}'

    def salir(self):
        if self.conexion:
            self.conexion.close()
        self.destroy()


if __name__ == '__main__':
    App().mainloop()
