from flask import Flask, render_template, request
from scraping_script import obtener_articulos_diario_sin_fronteras
import mysql.connector
from mysql.connector import Error
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

# Crear la carpeta "descargas" si no existe
if not os.path.exists('descargas'):
    os.makedirs('descargas')

# Configurar la conexión a la base de datos
def crear_conexion():
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='web_scraping_db'
        )
        if conexion.is_connected():
            print("Conexión exitosa a la base de datos")
        return conexion
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Función para guardar los artículos en la base de datos sin duplicados
def guardar_articulos(articulos):
    conexion = crear_conexion()
    if conexion is None:
        return

    try:
        cursor = conexion.cursor()
        for articulo in articulos:
            cursor.execute("SELECT id FROM articulos WHERE url_articulo = %s", (articulo['url_articulo'],))
            resultado = cursor.fetchone()

            if resultado:
                print(f"El artículo '{articulo['titulo']}' ya existe en la base de datos.")
            else:
                cursor.execute("""
                    INSERT INTO articulos (diario, titulo, url_articulo, imagen, contenido, fecha, autor)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    articulo['diario'],
                    articulo['titulo'],
                    articulo['url_articulo'],
                    articulo['imagen'],
                    articulo['contenido'],
                    articulo['fecha'],
                    articulo['autor']
                ))
                print(f"Artículo '{articulo['titulo']}' guardado correctamente en la base de datos.")
        
        conexion.commit()
    except Error as e:
        print(f"Error al guardar los artículos: {e}")
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

# Función para exportar los artículos de la base de datos a un archivo Excel
def exportar_articulos_a_excel():
    conexion = crear_conexion()
    if conexion is None:
        return

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f'descargas/articulos_{timestamp}.xlsx'

        query = "SELECT * FROM articulos"
        df = pd.read_sql(query, conexion)

        df.to_excel(nombre_archivo, index=False)
        print(f"Artículos exportados exitosamente a {nombre_archivo}")

    except Error as e:
        print(f"Error al exportar los artículos a Excel: {e}")
    finally:
        if conexion.is_connected():
            conexion.close()

@app.route('/')
def index():
    url = request.args.get('url')
    page = int(request.args.get('page', 1))
    articulos = []
    diario = 'Diario Sin Fronteras'

    if url and "diariosinfronteras.com.pe" in url:
        try:
            articulos = obtener_articulos_diario_sin_fronteras(url)

            if articulos:
                guardar_articulos(articulos)
                exportar_articulos_a_excel()
        except Exception as e:
            print(f"Error al procesar la URL: {url}. Error: {e}")

    total_articulos = len(articulos)
    per_page = 9
    total_pages = (total_articulos // per_page) + (1 if total_articulos % per_page > 0 else 0)
    start = (page - 1) * per_page
    end = start + per_page

    return render_template('index.html', articulos=articulos[start:end], diario=diario, page=page, total_pages=total_pages)

if __name__ == '__main__':
    app.run(debug=True)
