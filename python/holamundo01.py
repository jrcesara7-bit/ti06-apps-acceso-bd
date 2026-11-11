"""HolaMundo01 en Python. Se conecta a MySQL, ejecuta un SELECT y muestra los registros en consola.

Uso:  python holamundo01.py              lista a todos los trabajadores
      python holamundo01.py Fontanero    filtra por oficio (el valor viaja como parámetro)
"""
import sys

import pymysql

import config

SQL = """
    SELECT t.id_trabajador, t.nombre, t.oficio, t.tarifa_hr, s.nombre AS supervisor
    FROM trabajador t
    LEFT JOIN trabajador s ON s.id_trabajador = t.id_supv
    WHERE t.oficio LIKE %s
    ORDER BY t.nombre"""


def imprimir_tabla(columnas, filas):
    """Imprime los registros alineados, calculando el ancho de cada columna."""
    textos = [[str(v) for v in fila] for fila in filas]
    anchos = [max(len(c), *(len(f[i]) for f in textos)) if textos else len(c) for i, c in enumerate(columnas)]
    linea = '+' + '+'.join('-' * (a + 2) for a in anchos) + '+'
    print(linea)
    print('|' + '|'.join(f' {c:<{a}} ' for c, a in zip(columnas, anchos)) + '|')
    print(linea)
    for fila in textos:
        print('|' + '|'.join(f' {v:<{a}} ' for v, a in zip(fila, anchos)) + '|')
    print(linea)


def main():
    if not config.USUARIO:
        sys.exit('Falta DB_USER. Copia .env.example como .env y llena tus datos.')
    oficio = sys.argv[1] if len(sys.argv) > 1 else '%'
    try:
        conexion = pymysql.connect(host=config.HOST, port=config.PUERTO, user=config.USUARIO,
                                   password=config.CLAVE or '', database=config.BASE)
    except pymysql.MySQLError as error:
        sys.exit(f'No se pudo conectar: {error.args[-1]}')
    try:
        print(f'Conectado a {config.BASE} en {config.HOST}:{config.PUERTO} como {config.USUARIO}')
        with conexion.cursor() as cursor:
            # El driver escapa el parámetro. Nunca se arma el SQL con f-strings ni concatenando texto.
            cursor.execute(SQL, (oficio,))
            columnas = [d[0] for d in cursor.description]
            filas = cursor.fetchall()
        imprimir_tabla(columnas, filas)
        print(f'{len(filas)} registro(s)')
    finally:
        conexion.close()   # siempre se cierra la conexión


if __name__ == '__main__':
    main()
