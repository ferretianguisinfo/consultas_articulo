import os
from flask import Flask, render_template, request, send_file, redirect
import pyodbc
import pandas as pd
from io import BytesIO

app = Flask(__name__)

# Configuración de la conexión
server = 'SERVERINSAC5\\WINCAJASERVER'
database = 'Ferretianguis'
username = 'sa'
password = 'Wincaja20'

tareas = {}
@app.route('/asignar_tarea', methods=['POST'])
def asignar_tarea():
    sku = request.form['sku']
    tarea = request.form['tarea']
    if sku not in tareas:
        tareas[sku] = []
    tareas[sku].append({'tarea': tarea, 'finalizada': False})
    print(f"Tarea asignada al SKU {sku}: {tarea}")
    return redirect('/')

@app.route('/finalizar_tarea', methods=['POST'])
def finalizar_tarea():
    sku = request.form['sku']
    tarea_index = int(request.form['tarea_index'])
    if sku in tareas and 0 <= tarea_index < len(tareas[sku]):
        tareas[sku][tarea_index]['finalizada'] = True
        print(f"Tarea finalizada para el SKU {sku}: {tareas[sku][tarea_index]['tarea']}")
    return redirect('/')

@app.route('/')
def index():
    # Variables para filtros
    articulo = request.args.get('articulo', '').strip()
    nombre = request.args.get('nombre', '').strip()
    codigo_barras = request.args.get('codigo_barras', '').strip()
    descripcion_subfamilia = request.args.get('descripcion_subfamilia', '').strip()
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

        # Crear un cursor para ejecutar las consultas
        cursor = connection_string.cursor()

        # Construcción de la consulta SQL
        query = '''
            SELECT 
                a.Articulo,
                a.CodigoBarras,
                a.Subfamilia,
                a.Nombre,
                s.Descripcion AS SubfamiliaDescripcion,
                p1.Precio1IVAUV,
                p2.Precio2IVAUV,
                p3.Precio3IVAUV,
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

        # Ajustar el orden según la selección del usuario
        if orden == 'valor':
            query += " ORDER BY vt.VentaUnidadPeriodo DESC, a.Nombre ASC"
        else:
            query += " ORDER BY a.Nombre ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Cerrar conexiones
        cursor.close()
        connection_string.close()

        return render_template('index.html', rows=rows, articulo=articulo, nombre=nombre,
                               codigo_barras=codigo_barras, descripcion_subfamilia=descripcion_subfamilia, orden=orden)

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
                p1.Precio1IVAUV,
                p2.Precio2IVAUV,
                p3.Precio3IVAUV,
                pn.UltimoCostoNeto,
                c.Cantidad,
                vt.VentaUnidadPeriodo,
                CASE 
                    WHEN pn.UltimoCostoNeto > 0 THEN 
                        ((p1.Precio1IVAUV - pn.UltimoCostoNeto) / pn.UltimoCostoNeto)*100
                    ELSE 
                        NULL
                END AS PorcentajeGanancia1,
                CASE 
                    WHEN pn.UltimoCostoNeto > 0 THEN 
                        ((p2.Precio2IVAUV - pn.UltimoCostoNeto) / pn.UltimoCostoNeto)*100
                    ELSE 
                        NULL
                END AS PorcentajeGanancia2,
                CASE 
                    WHEN pn.UltimoCostoNeto > 0 THEN 
                        ((p3.Precio3IVAUV - pn.UltimoCostoNeto) / pn.UltimoCostoNeto)*100
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
        return send_file(output, as_attachment=True, download_name='articulos.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

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
    #app.run(debug=False)   
@app.route('/consulta')
def consulta():
    url = "https://consultas-articulo.onrender.com/"
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify(response.json())  # Retorna los datos obtenidos
    return jsonify({"error": "No se pudo obtener información"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
