import sqlite3
import os
import time
from scryfall import ScryFall

RUTA_BD = "magic.db"


def get_connection():
    """Obtiene una única conexión para toda la ejecución"""
    conn = sqlite3.connect(RUTA_BD, timeout=15)
    # Habilitar el modo WAL para mejorar la concurrencia
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def tablas_contienen_datos(conn):
    """Versión más robusta, usando la conexión proporcionada"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='colecciones'")
        if not cursor.fetchone():
            return False

        cursor.execute("SELECT COUNT(*) FROM colecciones")
        return cursor.fetchone()[0] > 0
    except sqlite3.Error as e:
        print(f"Error verificando datos en tablas: {e}")
        return False


def inicializar_base_de_datos():
    """Crea las tablas con estructura mejorada"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS colecciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scryfall_id TEXT UNIQUE,
            nombre TEXT NOT NULL,
            codigo TEXT NOT NULL UNIQUE,
            fecha_salida TEXT NOT NULL,
            total_cartas INTEGER NOT NULL,
            imagen TEXT,
            icon_svg TEXT,
            ultima_actualizacion TEXT
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cartas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scryfall_id TEXT UNIQUE,
            nombre TEXT NOT NULL,
            coleccion_id INTEGER,
            numero_serie TEXT NOT NULL,
            imagen_url TEXT,
            color TEXT,
            rareza TEXT,
            obtenida BOOLEAN DEFAULT 0,
            FOREIGN KEY (coleccion_id) REFERENCES colecciones(id),
            UNIQUE(scryfall_id, coleccion_id)
        )""")

        if not tablas_contienen_datos(conn):
            print("Inicializando datos básicos...")
            cursor.execute("""
            INSERT OR IGNORE INTO colecciones 
            (nombre, codigo, fecha_salida, total_cartas, imagen)
            VALUES (?, ?, ?, ?, ?)
            """, ("Colección Ejemplo", "EXM", "2023-01-01", 100, "ruta/imagen.png"))

            if input("¿Sincronizar con ScryFall ahora? (s/n): ").lower() == "s":
                sincronizar_colecciones(conn)

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
    finally:
        conn.close()


def sincronizar_colecciones(conn):
    """Actualiza las colecciones desde ScryFall usando la conexión proporcionada"""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print("Obteniendo colecciones desde ScryFall...")
            scryfall = ScryFall()
            colecciones = scryfall.buscar_colecciones()
            print(f"Se encontraron {len(colecciones)} colecciones para sincronizar.")

            cursor = conn.cursor()
            for i, col in enumerate(colecciones, 1):
                print(f"Sincronizando colección {i}/{len(colecciones)}: {col['name']} (Código: {col['code']})")
                cursor.execute("""
                INSERT OR REPLACE INTO colecciones 
                (scryfall_id, nombre, codigo, fecha_salida, total_cartas, icon_svg, ultima_actualizacion)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    col["id"],
                    col["name"],
                    col["code"],
                    col["released_at"],
                    col["card_count"],
                    col["icon_svg_uri"]
                ))
            conn.commit()
            print(f"✅ Sincronizadas {len(colecciones)} colecciones")
            break  # Salir del bucle si la sincronización tiene éxito
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print(f"Intento {attempt + 1}/{max_retries} falló: Base de datos bloqueada. Esperando 3 segundos...")
                time.sleep(3)
                if attempt == max_retries - 1:
                    print(f"❌ Error sincronizando después de {max_retries} intentos: {str(e)}")
                    print("Sugerencia: Asegúrate de que no haya otras instancias de la aplicación ejecutándose.")
                    print("También verifica que tengas permisos de escritura en el directorio actual.")
            else:
                print(f"❌ Error sincronizando: {str(e)}")
                break
        except Exception as e:
            print(f"❌ Error sincronizando: {str(e)}")
            break


def mostrar_menu_sincronizacion():
    """Muestra el menú de sincronización"""
    print("\n" + "=" * 50)
    print("Gestión de Base de Datos Magic Collection")
    print("=" * 50)

    conn = get_connection()
    try:
        if tablas_contienen_datos(conn):
            opcion = input("\n¿Qué deseas hacer?\n1. Sincronizar colecciones con ScryFall\n2. Salir\n> ")
            if opcion == "1":
                sincronizar_colecciones(conn)
        else:
            print("\nInicializando base de datos...")
            if input("¿Sincronizar con ScryFall ahora? (s/n): ").lower() == "s":
                sincronizar_colecciones(conn)
    finally:
        conn.close()


def obtener_colecciones():
    """Versión compatible con el main.py existente"""
    conn = sqlite3.connect(RUTA_BD, timeout=15)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, codigo, fecha_salida, total_cartas, imagen 
            FROM colecciones 
            ORDER BY date(fecha_salida) DESC
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener colecciones: {e}")
        return []
    finally:
        conn.close()


if __name__ == "__main__":
    # Verificar si la BD existe
    if not os.path.exists(RUTA_BD):
        inicializar_base_de_datos()
    else:
        mostrar_menu_sincronizacion()