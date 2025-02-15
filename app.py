import os
from flask import Flask, render_template, request, send_file, redirect
import pyodbc
import pandas as pd
from io import BytesIO
import xlsxwriter


app = Flask(__name__)

# Configuración de la conexión
server = '192.168.1.40,1433'
database = 'Ferretianguis'
username = 'sa'
password = 'Wincaja20'

@app.route('/asignar_tarea', methods=['POST'])
def asignar_tarea():
    articulo_id = request.form['articulo_id']
    tarea = request.form['tarea']
    
    try:
        # Cadena de conexión y ejecución de consulta para asignar tarea
        connection_string = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password}'
        )

        cursor = connection_string.cursor()
        query = '''
            UPDATE Articulos
            SET Tareas = ?
            WHERE Articulo = ?
        '''
        cursor.execute(query, tarea, articulo_id)
        connection_string.commit()

        cursor.close()
        connection_string.close()
        
        return redirect('/')

    except Exception as e:
        return f"Error al asignar tarea: {e}"

@app.route('/eliminar_tarea', methods=['POST'])
def eliminar_tarea():
    articulo_id = request.form['articulo_id']
    
    try:
        # Cadena de conexión y ejecución de consulta para eliminar tarea
        connection_string = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password}'
        )

        cursor = connection_string.cursor()
        query = '''
            UPDATE Articulos
            SET Tareas = NULL
            WHERE Articulo = ?
        '''
        cursor.execute(query, articulo_id)
        connection_string.commit()

        cursor.close()
        connection_string.close()
        
        return redirect('/')

    except Exception as e:
        return f"Error al eliminar tarea: {e}"

@app.route('/')
def index():
    # Variables para filtros
    articulo = request.args.get('articulo', '').strip()
    nombre = request.args.get('nombre', '').strip()
    codigo_barras = request.args.get('codigo_barras', '').strip()
    descripcion_subfamilia = request.args.get('descripcion_subfamilia', '').strip()
    tareas = request.args.get('tareas', '').strip()
    orden = request.args.get('orden', 'nombre').strip()  # Captura el parámetro de orden, por defecto 'nombre'

    try:
        # Cadena de conexión
        connection_string = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password}'
        )

        cursor = connection_string.cursor()

        # Construcción de la consulta SQL
        query = '''
            SELECT 
                a.Articulo,
                a.CodigoBarras,
                a.Subfamilia,
                a.Nombre,
                s.Descripcion AS SubfamiliaDescripcion,
                CAST(p1.Precio1IVAUV AS DECIMAL(10,2)) AS Precio1IVAUV,
                CAST(p2.Precio2IVAUV AS DECIMAL(10,2)) AS Precio2IVAUV,
                CAST(p3.Precio3IVAUV AS DECIMAL(10,2)) AS Precio3IVAUV,
                pn.UltimoCostoNeto,
                c.Cantidad,
                vt.VentaUnidadPeriodo,
                CASE 
                    WHEN pn.UltimoCostoNeto > 0 THEN 
                        CAST(((p1.Precio1IVAUV - pn.UltimoCostoNeto) / pn.UltimoCostoNeto) * 100 AS INT)
                    ELSE 
                        NULL
                END AS PorcentajeGanancia1,
                CASE 
                    WHEN pn.UltimoCostoNeto > 0 THEN 
                        CAST(((p2.Precio2IVAUV - pn.UltimoCostoNeto) / pn.UltimoCostoNeto) * 100 AS INT)
                    ELSE 
                        NULL
                END AS PorcentajeGanancia2,
                CASE 
                    WHEN pn.UltimoCostoNeto > 0 THEN 
                        CAST(((p3.Precio3IVAUV - pn.UltimoCostoNeto) / pn.UltimoCostoNeto) * 100 AS INT)
                    ELSE 
                        NULL
                END AS PorcentajeGanancia3,
                a.Tareas
            FROM Articulos a
            LEFT JOIN Subfamilias s ON a.Subfamilia = s.Subfamilia
            LEFT JOIN Qv4PreciosNo1 p1 ON a.Articulo = p1.Articulo AND p1.TipoTienda = '3'
            LEFT JOIN Qv4PreciosNo2 p2 ON a.Articulo = p2.Articulo AND p2.TipoTienda = '3'
            LEFT JOIN Qv4PreciosNo3 p3 ON a.Articulo = p3.Articulo AND p3.TipoTienda = '3'
            LEFT JOIN QV4ListaPrecioConCosto pn ON a.Articulo = pn.Articulo AND pn.DescAlmacen='Acedis' AND pn.TipoTienda = '1'
            LEFT JOIN ArticulosyProveedores vt ON a.Articulo = vt.Articulo AND vt.DescAlmacen='Acedis' AND vt.Prioridad = '1'
            LEFT JOIN QxxDetalleCompra c ON a.Articulo = c.Articulo
            WHERE 1=1
        '''
        params = []

        if articulo:
            query += " AND a.Articulo LIKE ?"
            params.append(f'%{articulo}%')
        if nombre:
            query += " AND a.Nombre LIKE ?"
            params.append(f'%{nombre}%')
        if codigo_barras:
            query += " AND a.CodigoBarras LIKE ?"
            params.append(f'%{codigo_barras}%')
        if descripcion_subfamilia:
            query += " AND s.Descripcion LIKE ?"
            params.append(f'%{descripcion_subfamilia}%')
        if tareas:
            query += " AND a.Tareas LIKE ?"
            params.append(f'%{tareas}%')

        if orden == 'valor':
            query += " ORDER BY vt.VentaUnidadPeriodo DESC, a.Nombre ASC"
        else:
            query += " ORDER BY a.Nombre ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        cursor.close()
        connection_string.close()

        return render_template('index.html', rows=rows, articulo=articulo, nombre=nombre,
                               codigo_barras=codigo_barras, descripcion_subfamilia=descripcion_subfamilia, tareas=tareas, orden=orden)

    except Exception as e:
        return f"Error al intentar conectar o ejecutar la consulta: {e}"

    
@app.route('/download_excel')
def download_excel():
    articulo = request.args.get('articulo', '').strip()
    nombre = request.args.get('nombre', '').strip()
    codigo_barras = request.args.get('codigo_barras', '').strip()
    descripcion_subfamilia = request.args.get('descripcion_subfamilia', '').strip()

    try:
        connection_string = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password}'
        )
        cursor = connection_string.cursor()

        query = '''
            SELECT 
                a.Articulo,
                a.CodigoBarras,
                a.Subfamilia,
                a.Nombre,
                s.Descripcion AS SubfamiliaDescripcion,
                CAST(p1.Precio1IVAUV AS DECIMAL(10,2)) AS Precio1IVAUV,
                CAST(p2.Precio2IVAUV AS DECIMAL(10,2)) AS Precio2IVAUV,
                CAST(p3.Precio3IVAUV AS DECIMAL(10,2)) AS Precio3IVAUV,
                pn.UltimoCostoNeto,
                c.Cantidad,
                vt.VentaUnidadPeriodo,
                CASE 
                    WHEN pn.UltimoCostoNeto > 0 THEN 
                        CAST(((p1.Precio1IVAUV - pn.UltimoCostoNeto) / pn.UltimoCostoNeto) * 100 AS INT)
                    ELSE 
                        NULL
                END AS PorcentajeGanancia1,
                CASE 
                    WHEN pn.UltimoCostoNeto > 0 THEN 
                        CAST(((p2.Precio2IVAUV - pn.UltimoCostoNeto) / pn.UltimoCostoNeto) * 100 AS INT)
                    ELSE 
                        NULL
                END AS PorcentajeGanancia2,
                CASE 
                    WHEN pn.UltimoCostoNeto > 0 THEN 
                        CAST(((p3.Precio3IVAUV - pn.UltimoCostoNeto) / pn.UltimoCostoNeto) * 100 AS INT)
                    ELSE 
                        NULL
                END AS PorcentajeGanancia3
            FROM Articulos a
            LEFT JOIN Subfamilias s ON a.Subfamilia = s.Subfamilia
            LEFT JOIN Qv4PreciosNo1 p1 ON a.Articulo = p1.Articulo AND p1.TipoTienda = '3'
            LEFT JOIN Qv4PreciosNo2 p2 ON a.Articulo = p2.Articulo AND p2.TipoTienda = '3'
            LEFT JOIN Qv4PreciosNo3 p3 ON a.Articulo = p3.Articulo AND p3.TipoTienda = '3'
            LEFT JOIN QV4ListaPrecioConCosto pn ON a.Articulo = pn.Articulo AND pn.DescAlmacen='Acedis' AND pn.TipoTienda = '1'
            LEFT JOIN ArticulosyProveedores vt ON a.Articulo = vt.Articulo AND vt.DescAlmacen='Acedis' AND vt.Prioridad = '1'
            LEFT JOIN QxxDetalleCompra c ON a.Articulo = c.Articulo
            WHERE 1=1
        '''
        params = []
        if articulo:
            query += " AND a.Articulo LIKE ?"
            params.append(f'%{articulo}%')
        if nombre:
            query += " AND a.Nombre LIKE ?"
            params.append(f'%{nombre}%')
        if codigo_barras:
            query += " AND a.CodigoBarras LIKE ?"
            params.append(f'%{codigo_barras}%')
        if descripcion_subfamilia:
            query += " AND s.Descripcion LIKE ?"
            params.append(f'%{descripcion_subfamilia}%')
        query += " ORDER BY a.Nombre ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convertir los resultados a un DataFrame de pandas
        columns = [desc[0] for desc in cursor.description]
        data = pd.DataFrame.from_records(rows, columns=columns)

        # Guardar el DataFrame en un archivo Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            data.to_excel(writer, index=False, sheet_name='Articulos')
        output.seek(0)

        # Enviar el archivo al cliente
        return send_file(output, as_attachment=True, download_name='articulos.xlsx')



    except Exception as e:
        return f"Error al intentar generar el archivo Excel: {e}"

@app.route('/proveedores/<articulo>')
def proveedores(articulo):
    try:
        # Conectar a la base de datos
        connection_string = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=' + server + ';'
            'DATABASE=' + database + ';'
            'UID=' + username + ';'
            'PWD=' + password
        )

        # Crear un cursor para ejecutar la consulta
        cursor = connection_string.cursor()

        # Consulta para obtener los proveedores relacionados con el artículo
        query = '''
            SELECT 
                Articulo, 
                Proveedor, 
                NombreProvedor,
                DescAlmacen
            FROM ArticulosyProveedores
            WHERE DescAlmacen='Acedis' AND Articulo = ?
        '''
        cursor.execute(query, (articulo,))

        # Obtener los resultados
        rows = cursor.fetchall()

        # Cerrar conexión
        cursor.close()
        connection_string.close()

        # Renderizar la plantilla de proveedores
        return render_template('proveedores.html', rows=rows, articulo=articulo)

    except Exception as e:
        return f"Error al intentar conectar o ejecutar la consulta: {e}"

@app.route('/compras/<articulo>')
def compras(articulo):
    try:
        # Conectar a la base de datos
        connection_string = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=' + server + ';'
            'DATABASE=' + database + ';'
            'UID=' + username + ';'
            'PWD=' + password
        )

        # Crear un cursor para ejecutar la consulta
        cursor = connection_string.cursor()

        # Consulta para obtener los proveedores relacionados con el artículo 
        query = '''
            SELECT 
                Articulo, 
                Cantidad, 
                ValorCosto,
                IVA,
                ValorCostoNeto
            FROM QxxDetalleCompra
            WHERE Articulo = ?
        '''
        cursor.execute(query, (articulo,))

        # Obtener los resultados
        rows = cursor.fetchall()

        # Cerrar conexión
        cursor.close()
        connection_string.close()

        # Renderizar la plantilla de proveedores
        return render_template('compras.html', rows=rows, articulo=articulo)

    except Exception as e:
        return f"Error al intentar conectar o ejecutar la consulta: {e}"
    
@app.route('/ventas/<articulo>')
def ventas(articulo):
    try:
        # Conectar a la base de datos
        connection_string = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=' + server + ';'
            'DATABASE=' + database + ';'
            'UID=' + username + ';'
            'PWD=' + password
        )

        # Crear un cursor para ejecutar la consulta
        cursor = connection_string.cursor()

        # Consulta para obtener los proveedores relacionados con el artículo 
        query = '''
            SELECT 
                Articulo, 
                NombreArticulo,
                NombreProvedor,
                VentaUnidadPeriodo,
                VentaValorPeriodo
            FROM ArticulosyProveedores
            WHERE DescAlmacen='Acedis' AND Articulo = ?
        '''
        cursor.execute(query, (articulo,))

        # Obtener los resultados
        rows = cursor.fetchall()

        # Cerrar conexión
        cursor.close()
        connection_string.close()

        # Renderizar la plantilla de proveedores
        return render_template('ventas.html', rows=rows, articulo=articulo)

    except Exception as e:
        return f"Error al intentar conectar o ejecutar la consulta: {e}"


#if __name__ == '__main__':
 #   app.run(debug=False)   
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 1000))
    app.run(host='0.0.0.0', port=port, debug=True)


